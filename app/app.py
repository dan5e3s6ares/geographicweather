import json
from processar import main


def handler(event, context):
    try:
        event = json.loads(event['body'])
        result = json.loads(event)
        cod = result['cod']
        if cod == 'flerifbwet7864poigjfgdbçcr287456brtgfgh':
            mapa = result['mapa']
            relid = result['relid']
            url = result['url']
            token = result['token']
            main(mapa, relid, token, url)
            return {
                'statusCode': 200,
                'body': json.dumps('Sweet')
            }
        else:
            print('erro de código')
            return {
                'statusCode': 400,
                'body': json.dumps('Bitter')
            }
    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps('Bitter')
        }
