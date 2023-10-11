GET_DRAFT_ORDERS = """
query {
  draftOrders(first: 250,after: "eyJsYXN0X2lkIjoxMTM0OTcyMTc0NjEzLCJsYXN0X3ZhbHVlIjoiMTEzNDk3MjE3NDYxMyJ9") {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        name
        createdAt
        updatedAt
        customer {
          firstName
          lastName
        }
      }
    }
  }
}
"""

GET_DRAFT_ORDER =consulta = """
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
          metafields(first: 1, namespace: "custom") {{
            edges {{
              node {{
                key
                value
              }}
            }}
          }}
        }}
        invoiceUrl
        lineItems(first: 20) {{
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
                variants(first: 1) {{  # Agregamos este campo para obtener el SKU
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
