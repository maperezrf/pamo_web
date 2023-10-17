from datetime import datetime

def make_json(res):
    for i in range(len(res)):
        res[i]['node']['createdAt'] = datetime.strptime((res[i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['updatedAt'] = datetime.strptime((res[i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['name'] = int(res[i]['node']['name'][2:])
    return(res)