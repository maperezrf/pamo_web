function formatNumber(number) {
    return (number).toLocaleString('es-CO', {
      style: 'currency',
      currency: 'COP'
    }).replace(/,\d{2}/g, '');
  }