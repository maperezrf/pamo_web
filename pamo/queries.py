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

GET_PRODUCTS = """
query {{
   products(first:1 {cursor}) {{
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
          variants(first: 1) {{
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
}} """

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
          variants(first: 1) {{
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