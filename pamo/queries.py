GET_DRAFT_ORDERS = """
query {{
  draftOrders(first: 250 {cursor}){{
    pageInfo {{
      hasNextPage
      endCursor
    }}
    edges {{
      node {{
        id
        name
        createdAt
        updatedAt
        totalPrice
        customer {{
          firstName
          lastName
        }}
      }}
    }}
  }}
}}
"""

GET_DRAFT_ORDER = """
{{
  draftOrders(first: 1 query:"id:{}") {{
    edges {{
      node {{
        id
        name
        totalPrice
        createdAt
        updatedAt
          appliedDiscount {{
            amount
        }}
        customer {{
          displayName
          email
          defaultAddress {{
            company
            phone
          }}
          metafields(first: 2, namespace: "custom") {{
            edges {{
              node {{
                key
                value
              }}
            }}
          }}
        }}
        invoiceUrl
        lineItems(first: 250) {{
          edges {{
            node {{
              title
              originalUnitPrice
              quantity
              product {{
                images(first: 1) {{
                  edges {{
                    node {{
                      originalSrc
                    }}
                  }}
                }}
                variants(first: 1) {{ 
                  edges {{
                    node {{
                      sku
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

GET_DRAFT_ORDER_UPDATE = """
{{
  draftOrders(first: 1 query:"id:{}") {{
    edges {{
      node {{
        id
        name
        createdAt
        updatedAt
        totalPrice
        customer {{
          firstName
          lastName
        }}
      }}
    }}
  }}
}}
"""

GET_PRODUCTS ="""
{{
   products(first: 249 {cursor})  {{
      pageInfo {{
      hasNextPage
      endCursor
      }}
      edges {{
        node {{
          id
        	tags
          title
          vendor
          status
          variants(first: 250) {{
            edges {{
              node {{
                price
                compareAtPrice
                sku
                barcode
                inventoryQuantity
            }}
          }}
        }}
      }}
    }}
  }}
}}"""

UPDATE_QUERY = """mutation UpdateProductAndVariantAndAdjustInventory(
  {productInput}
  {variantInput}
  {inventoryAdjustInput}
  ){{
  {productUpdateq}
  {productVariantUpdateq}
  {inventoryAdjustQuantity}
}}"""

UPTADE_PRODUCT = """
  productUpdate(input: $productInput) {
    userErrors {
      field
      message
    }
  }
"""

PRODUCT_VARIANT_UPDATE = """
  productVariantUpdate(input: $variantInput) {
    userErrors {
      field
      message
    }
  }
"""

INVENTORY_ADJUST ="""
  inventoryAdjustQuantity(input: $inventoryAdjustInput) {
  inventoryLevel {
    available
    }
  }
"""

GET_VARIANT_ID = """{{
products(first: 1, query: "sku:{skus}") {{
    edges {{
    node {{
        id
        variants(first: 1) {{
        edges {{
            node {{
            id
            sku
            }}
        }}
        }}
    }}
    }}
}}
}}
"""

GET_INVENTORY = """
{{
products(first: 1, query: "sku:{sku}") {{
    edges {{
    node {{
        id
        variants(first: 1) {{
        edges {{
            node {{
            sku
            inventoryQuantity
            }}
        }}
        }}
    }}
    }}
}}
}}
"""



GET_VARIANT = """
{{
  productVariants(first: 250, query: "{skus}") {{
    edges {{
      node {{
        id
        price
        compareAtPrice
        sku
        barcode
        inventoryQuantity
        inventoryItem {{
          id
          inventoryLevels(first: 1) {{
            edges {{
              node {{
                id
              }}
            }}
          }}
        }}
        }} 
      }}
    }}
}}
"""

GET_PRODUCT= """
query {{
   product(id : "gid://shopify/Product/{id}") {{
          id
        	tags
          title
          vendor
          status
          published: publishedInContext(context: {{country: CO}})
  }}
}}
  """