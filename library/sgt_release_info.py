#!/usr/bin/python
# coding=utf-8

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
import requests
import json
import os
from datetime import datetime


###DOCUMENTATION = r'''
###---
###module: onefcc_snow_task
###
###short_description: Modulo de release para ONEFCC Service Now
###
###version_added: "1.0.0"
###
###description: Modulo para crear, cerrar y obtener informacion acerca de las releases.
###
###options:
###    state:
###        description: Es para indicar la opcion a realizar dentro de la task
###            - info_task. Para obtener informacion a cerca de la task
###            - incomplete.
###        required: false
###        type: bool
###    task:
###        description: Numero de la tarea a buscar, requerido si info_task esta presente
###        required: true
###        type: str
###    
###
#### Specify this value according to your collection
#### in format of namespace.collection.doc_fragment_name
###extends_documentation_fragment:
###    - my_namespace.my_collection.my_doc_fragment_name
###
###author:
###    - Marco Rea (@x25241)
###'''
###
###EXAMPLES = r'''
#### Pass in a message
###- name: Test with a message
###  my_namespace.my_collection.my_test:
###    name: hello world
###
#### pass in a message and have changed true
###- name: Test with a message and changed output
###  my_namespace.my_collection.my_test:
###    name: hello world
###    new: true
###
#### fail the module
###- name: Test failure of the module
###  my_namespace.my_collection.my_test:
###    name: fail me
###'''
###
###RETURN = r'''
#### These are examples of possible return values, and in general should use other names for return values.
###original_message:
###    description: The original name param that was passed in.
###    type: str
###    returned: always
###    sample: 'hello world'
###message:
###    description: The output message that the test module generates.
###    type: str
###    returned: always
###    sample: 'goodbye'
###'''

def show_values(response, other_values, **module_args):
    
    content_json = response.json()

    if module_args["filter"] and response.status_code in [200,201]:
        new_values = {
            "result":{
                "sys_id": content_json["result"]["sys_id"],
                "number": content_json["result"]["number"],
                "state": content_json["result"]["state"],
                "company": content_json["result"]["company"],
                "parent": content_json["result"]["parent"],
                "assignment_group": content_json["result"]["assignment_group"],
                "u_requested_group": content_json["result"]["u_requested_group"],
                "u_reason": content_json["result"]["u_reason"],
                "u_risk": content_json["result"]["u_risk"],
                "short_description": content_json["result"]["short_description"],
                "description": content_json["result"]["description"],
                "u_justification": content_json["result"]["u_justification"],
                "u_implementation_plan": content_json["result"]["u_implementation_plan"],
                "u_preproduction_proposed_date": content_json["result"]["u_preproduction_proposed_date"],
                "u_start_date": content_json["result"]["u_start_date"],
                "u_end_date": content_json["result"]["u_end_date"],
                "u_backout_plan": content_json["result"]["u_backout_plan"],
                "u_risk_and_impact_analysis": content_json["result"]["u_risk_and_impact_analysis"],
                "u_test_plan": content_json["result"]["u_test_plan"]
            }
        }

        new_values["result"].update(other_values)
    
    else:
        new_values = content_json


    return new_values

def info(release_number, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] 
    params={
        "sysparm_query": "number="+str(release_number),
        "sysparm_display_value": "true"
    }

    try:
        response = requests.get(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            params=params,
            timeout=module_args["timeout"]
        )

        new_values = show_values(response, { "old_state": "" }, **module_args)
        response._content = json.dumps(new_values).encode('utf8') 

    except Exception as e:
        response = {"mensaje": "ERROR, release could not get information: "+str(release_number)+": " + str(e)}

    return response

def validateOptions(module):
    
    if module.params["state"] == "info":
        return info(**module.params)

def run_module():
    
    module_args = {
        "state": {
            "default": "info",
            "choices": [
                "info"
            ]
        },
        #Generals
        "sn_user": {"required": True, "type": "str"},
        "sn_pass": {"required": True, "type": "str", "no_log": True},
        "sn_base": {"required": True, "type": "str", "default":"https://santandertest.service-now.com"},
        "sn_uri":  {"required": False, "type": "str", "default": "/api/now/v2/table/rm_release"},
        "timeout": {"required": False, "type": "int", "default": 300},
        "filter":  {"required": False, "type": "bool", "default": True},

        
        #For info
        "release":{ "type": "str" },

        
}

    result = dict(
        changed=False,
        original_message="",
        message=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[
            ('state', 'info', ('release', 'sn_user', 'sn_pass','sn_base','release'), False),
        ],
        required_together=[
            ('sn_user', 'sn_pass','sn_base'),
        ],
    )

    if module.check_mode:
        module.exit_json(**result)
    else:
        response = validateOptions(module)

    result["message"] = json.loads(response.text)

    if response.status_code == 200 or response.status_code == 201:
 
        resp = response.json()

        if "number" in resp["result"] or "sys_id" in resp["result"]:
            result['message'] = resp["result"]
            result['changed'] = True
        else:
            result['message'] = "Action could not be executed: "+module.params["state"]
            result['changed'] = False
            module.fail_json(msg="Response generic error: "+str(response), **result)
            
        module.exit_json(**result)

    else:
        module.fail_json(msg="Response generic error", **result)

def main():
    run_module()

if __name__ == '__main__':
    main()