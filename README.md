# Description
Simple SIP proxy for modification headers

# Requirements
`pip install twisted`

# Headers modification
Create file `headers.json`:

    {
        "request": { 
            "INVITE": {
                "Some-Header": "Some value"
            }
        },
        "response": {
            "200": {
                "FooHeader": "value"
            }
        }
    }

# Run
`./proxy.py --proxy-host proxyhost:5060 --client-host clienthost:5060 --target-host targethost:5060 --headers ./headers.json`

## Arguments

    --proxy-host PROXY_HOST Proxy host localhost:port ( or deafult port 5060 )
    --client-host CLIENT_HOST Client host localhost:port ( or deafult port 5060 )
    --target-host TARGET_HOST Target host localhost:port ( or deafult port 5060 )
    --headers HEADERS JSON file with headers