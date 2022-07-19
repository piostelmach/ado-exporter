import requests
import base64
import os
from flask import Flask

app = Flask(__name__)

app_port = os.environ.get('APP_PORT')  
pat = os.environ.get('PAT') 

@app.route('/health')
def health():
    return "OK"

@app.route('/metrics')
def run_metrics():
    authorization = str(base64.b64encode(bytes(':'+pat, 'ascii')), 'ascii')
    endpoint_pool = "https://dev.azure.com/organization/_apis/distributedtask/pools?api-version=7.1-preview.1"
    ado_healthy = "https://status.dev.azure.com/_apis/status/health?api-version=7.1-preview.1"

    headers = {'Accept': 'application/json','Authorization': 'Basic '+authorization}

    pool = requests.get(endpoint_pool,headers=headers)
    metrics = "# HELP azure_devops_agents_status show status of azure devops private agents. \n# TYPE azure_devops_agents_status gauge\n"

    for row in range(len(pool.json()['value'])): 
        pool_name = pool.json()['value'][row]['name']
        id_pool = pool.json()['value'][row]['id']
        endpoint_agents = "https://dev.azure.com/organization/_apis/distributedtask/pools/" + str(id_pool) + "/agents?api-version=6.0"

        agent = requests.get(endpoint_agents,headers=headers)   

        for row2 in range(len(agent.json()['value'])):
            agent_name = agent.json()['value'][row2]['name']
            agent_status = agent.json()['value'][row2]['status']

            if agent_status == "online":
                agent_status_bool = "1"
            else:
                agent_status_bool = "0"
            metrics += 'azure_devops_agents_status{pool_name="%s", agent_name="%s"} %s\n' % (pool_name, agent_name, agent_status_bool)

    health = requests.get(ado_healthy).json()
    health_message = health['status']['message']
    metrics += "# HELP azure_devops_health show status of azure devops health. \n# TYPE azure_devops_health gauge\n"

    if health_message == "Everything is looking good":
        health_status_bool = "1"
    else:
        health_status_bool = "0"

    metrics += 'azure_devops_health{azdevops_web_pages="status.dev.azure.com", message="%s"} %s\n' % (health_message, health_status_bool)
    return metrics

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=app_port)
