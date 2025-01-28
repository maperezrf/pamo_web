function show_loading(){
    Swal.fire({
        icon: 'info',
        title: 'Cargando',
        text: 'Por favor espera...',
        showConfirmButton: false,
        allowOutsideClick: false,
    })
  }

  function show_success(){
    Swal.fire({
        icon: "success",
        title: 'Proceso Exitoso',
        showConfirmButton: false,
        allowOutsideClick: false,
        timer: 1000
    })
  }








// Definir los medios de pago con su respectivo ID
const mediosDePago = [
  { "name": "Tarjeta Debito", "id": "6523" },
  { "name": "cash", "id": "6526" },
  { "name": "Nequi", "id": "6525" },
  { "name": "Addi Payment", "id": "8026" },
  { "name": "Pago Contra Entrega", "id": "6509" },
  { "name": "Bancolombia Transfer", "id": "6509" },
  { "name": "Wompi", "id": "6556" },
  { "name": "Tarjeta Crédito", "id": "6522" },
  { "name": "Daviplata", "id": "6520" },
  { "name": "Davivienda Transfer", "id": "6524" },
  { "name": "Checkout Mercado Pago", "id": "6534" },
  { "name": "Crédito", "id": "6507" }
];

// Función para obtener el ID del medio de pago seleccionado
function obtenerIdMedioDePago(nombreMedioPago) {
  const medioDePago = mediosDePago.find(medio => medio.name.toLowerCase() === nombreMedioPago.toLowerCase());
  return medioDePago ? medioDePago.id : "6507";  // Por defecto asignamos el ID de "Crédito" si no encuentra coincidencia
}

/**
 * Función para procesar las responsabilidades fiscales
 */
function obtenerResponsabilidadesFiscales(airtableItems) {
  const responsabilidadFiscalValues = [];
  airtableItems.forEach(item => {
    const responsabilidadFiscal = item.json['Responsabilidad fiscal '];
    if (responsabilidadFiscal && Array.isArray(responsabilidadFiscal)) {
        responsabilidadFiscalValues.push(...responsabilidadFiscal);
    }
  });
  return responsabilidadFiscalValues;
}

/**
 * Función para agregar retenciones según las condiciones
 */
function calcularRetenciones(subtotal, ciudad, responsabilidadFiscalValues) {
  let retentions = [{ id: 16584 }, { id: 13457 }, { id: 13464 }];  // Agregamos manualmente el id 13464

  // Verificar si la ciudad es Bogotá y el subtotal es mayor o igual a 1,270,000
  if (subtotal >= 1270000 && ciudad.toLowerCase() === 'bogota') {
      retentions.push({ id: 13457 });
  }

  // Verificar si responsabilidad_fiscal contiene el número 47 para agregar retención 13464
  responsabilidadFiscalValues.forEach((responsabilidad) => {
      if (responsabilidad.includes('47')) {
          retentions.push({ id: 13464 });
      }
  });

  return retentions;
}

/**
 * Función para calcular el IVA y el reteIVA si aplica
 */
function calcularIVA(valorBase, retentions, responsabilidadFiscalValues) {
  let iva = parseFloat(((valorBase * 19) / 100).toFixed(2));  // IVA del 19%
  let reteIVA = 0;

  // Verificar si aplicar reteIVA (15%)
  if (retentions.find(r => r.id === 13464) || responsabilidadFiscalValues.includes('47')) {
      reteIVA = parseFloat((iva * 0.15).toFixed(2));
      iva = parseFloat((iva - reteIVA).toFixed(2));  // Restar el reteIVA del IVA calculado
  }

  return { iva, reteIVA };
}

/**
 * Función para calcular el 2.5% si el código 13456 está presente
 */
function calcularImpuesto13456(valorBase, taxes) {
  let impuesto13456 = 0;
  if (taxes.find(t => t.id === 13456)) {
      impuesto13456 = parseFloat((valorBase * 0.025).toFixed(2));
      valorBase = parseFloat((valorBase - impuesto13456).toFixed(2));  // Restar el 2.5%
  }
  return { valorBase, impuesto13456 };
}

/**
 * Función para calcular el RETEICA
 * @param {number} valorBruto - El valor bruto de la factura sin IVA
 * @returns {number} - Retorna el valor del RETEICA calculado
 */
function calcularRETEICA(valorBruto) {
  // Aplicamos el 1.104% de RETEICA sobre el valor bruto sin IVA
  return parseFloat((valorBruto * 0.01104).toFixed(2));
}

/**
 * Función para calcular el total de la factura
 */
function calcularTotalFactura(items, retentions, responsabilidadFiscalValues, reteica) {
  let totalFactura = 0;

  items.forEach(item => {
    const quantity = Number(item.CANTIDAD_SKU || 0);
    const unitPriceWithoutIVA = Number(item.COSTO_SKU || 0);
    const discount = Number(item.DESCUENTO_SKU || 0);

    // 1. Calcular el Valor Base
    let valorBase = ((quantity * unitPriceWithoutIVA) - discount).toFixed(2);

    // 2. Calcular el IVA y reteIVA
    const { iva, reteIVA } = calcularIVA(valorBase, retentions, responsabilidadFiscalValues);

    // 3. Verificar si aplicar el impuesto 13456
    const taxes = [{ id: 16104 }, { id: 13456 }];
    const { valorBase: valorBaseAjustado } = calcularImpuesto13456(valorBase, taxes);
    valorBase = valorBaseAjustado;

    // 4. Sumar el valor base ajustado más el IVA
    totalFactura += parseFloat(valorBase) + parseFloat(iva);
  });

  // Restar el RETEICA del total de la factura
  totalFactura -= reteica;

  return totalFactura;
}

/**
 * Función para generar el JSON de respuesta
 */
function generarJsonRespuesta(httpRequestData, retentions, totalFactura, items, idMetodoDePago, reteica, pedido) {
  // Usar 'ORDEN_COMPRA' directamente desde el pedido y convertirlo a cadena
  const ordenCompraNumero = pedido.ORDEN_COMPRA ? pedido.ORDEN_COMPRA.toString() : '';

  return {
    document: {
      id: 26647
    },
    date: formattedDate,  // Tomamos la fecha ya definida en el código
    customer: {
      person_type: httpRequestData.results[0].person_type || '',
      id_type: httpRequestData.results[0].id_type?.code || '',
      identification: httpRequestData.results[0].identification || '',
      branch_office: httpRequestData.results[0].branch_office || '',
      name: httpRequestData.results[0].name || '',
      address: {
        address: httpRequestData.results[0].address?.address || '',
        city: {
          country_code: httpRequestData.results[0].address?.city?.country_code || '',
          country_name: httpRequestData.results[0].address?.city?.country_name || '',
          state_code: httpRequestData.results[0].address?.city?.state_code || '',
          city_code: httpRequestData.results[0].address?.city?.city_code || '',
          city_name: httpRequestData.results[0].address?.city?.city_name || ''
        },
        postal_code: "110911"
      },
      phones: (httpRequestData.results[0].phones || []).map(phone => ({
        indicative: phone.indicative || '',
        number: phone.number || '',
        extension: phone.extension ? String(phone.extension) : null
      })),
      contacts: (httpRequestData.results[0].contacts || []).map(contact => ({
        first_name: contact.first_name || '',
        last_name: contact.last_name || '',
        email: contact.email || '',
        phone: {
          indicative: contact.phone?.indicative || '',
          number: contact.phone?.number || '',
          extension: contact.phone?.extension ? String(contact.phone.extension) : null
        }
      }))
    },
    cost_center: 116,
    seller: 643,
    retentions: retentions,  // Retenciones calculadas
    reteica: reteica,        // Valor del RETEICA
    stamp: {
      send: false
    },
    mail: {
      send: false
    },
    observations: "Para pagos por bancos a nombre de FEPRIN S.A.S. tenga en cuenta la siguiente información:\nDAVIVIENDA Cuenta de Ahorros 457600102745\nBANCOLOMBIA Cuenta de Ahorros 17400002178\nRevisa nuestras políticas de cambios y garantías: www.pamo.co.",
    items: items.map(item => ({
      code: "SERV_TRANSF",
      description: `${item.SKU} - ${item.PRODUCTO}`,
      quantity: Number(item.CANTIDAD_SKU || 0),
      price: Number(item.COSTO_SKU || 0),
      discount: Number(item.DESCUENTO_SKU || 0),
      taxes: [{ id: 16104 }, { id: 13456 }]
    })),
    payments: [
      {
        id: idMetodoDePago,
        value: totalFactura.toFixed(2),
        due_date: formattedDate
      }
    ],
    additional_fields: {
      purchase_order: {
        number: ordenCompraNumero  // Aseguramos que sea una cadena
      }
    }
  };
}

// Obtener los datos desde el nodo HTTP Request7
const httpRequestData = $node['HTTP Request7'].json;

// Obtener las responsabilidades fiscales desde Airtable3
const airtableItems = $items('Airtable3');
const responsabilidadFiscalValues = obtenerResponsabilidadesFiscales(airtableItems);

// Verificar si existen resultados en HTTP Request7
if (!httpRequestData || !httpRequestData.results || !httpRequestData.results[0]) {
  return [{ json: { error: "No se encontraron datos en el JSON del cliente en HTTP Request7" } }];
}

// Obtener los pedidos desde HTTP Request13 y filtrar solo los que están en estado "4-ESTADO FINAL"
const pedidos = $node['HTTP Request13'].json.Value.filter(pedido => pedido.ESTADO_OC === "4-ESTADO FINAL");

// Procesar cada pedido en HTTP Request13 individualmente y devolver un JSON por cada uno en formato de texto
const resultados = pedidos.map(pedido => {
  // Obtener el subtotal y otros datos específicos para el pedido actual
  let subtotal = pedido.COSTO_TOT_OC || 0;  // Este valor ya está sin IVA
  let ciudad = httpRequestData.results[0].address?.city?.city_name || '';

  // Calcular las retenciones
  let retentions = calcularRetenciones(subtotal, ciudad, responsabilidadFiscalValues);

  // Calcular la base gravable sin IVA
  const valorBrutoSinIVA = pedido.PRODUCTOS.reduce((acc, item) => {
    const quantity = Number(item.CANTIDAD_SKU || 0);
    const unitPriceWithoutIVA = Number(item.COSTO_SKU || 0);
    return acc + (unitPriceWithoutIVA * quantity);
  }, 0);

  // Calcular el valor del RETEICA sobre la base gravable sin IVA
  let reteica = calcularRETEICA(valorBrutoSinIVA);

  // Calcular el total de la factura
  let totalFactura = calcularTotalFactura(pedido.PRODUCTOS, retentions, responsabilidadFiscalValues, reteica);

  // Obtener el método de pago para el pedido actual
  let metodoDePagoDesdePedido = pedido.CONDICION_PAGO || 'Crédito';
  const idMetodoDePago = obtenerIdMedioDePago(metodoDePagoDesdePedido);

  // Generar el JSON para este pedido y convertirlo a texto
  const jsonResultado = generarJsonRespuesta(
    httpRequestData,
    retentions,
    totalFactura,
    pedido.PRODUCTOS,
    idMetodoDePago,
    reteica,
    pedido
  );
  return { json: { jsonString: JSON.stringify(jsonResultado) } };
});

// Devolver el array de JSONs en formato de texto
return resultados;