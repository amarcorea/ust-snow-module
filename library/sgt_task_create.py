#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
import requests
import json
from datetime import datetime


###DOCUMENTATION = r'''
###---
###module: onefcc_snow_task
###
###short_description: Modulo de Tasks para ONEFCC Service Now
###
###version_added: "1.0.0"
###
###description: Modulo para crear, cerrar y obtener informacion acerca de las tasks.
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

def info(task_number, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] 
    params={"sysparm_query": "number="+str(task_number) }

    try:
        response = requests.get(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            params=params,
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, task could not get information: "+str(task_number)+": " + str(e)}
        #log("ERROR, no se pudo crear la release: " + str(e))

    return response

def create(release_number, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] 
    data={
        "top_task":             release_number,
        "u_release":            release_number,
        "start_date":           module_args["start_date"],
        "end_date":             module_args["end_date"],
        "short_description":    module_args["short_description"],
        "description":          module_args["description"],
        "u_state_to_resolve":   module_args["state_resolve"],
        "type":                 module_args["type"],
        "assignment_group":     module_args["group"],
        "order":                module_args["order"],
        "u_technology":         module_args["technology"],
        "u_version":            module_args["version"],
        "u_application":        module_args["application"]
    }

    try:
        response = requests.post(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            #params=params,
            data=json.dumps(data),
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, task could not created in release: "+str(release_number)+": " + str(e)}

    return response

def update(task_number, **module_args):

    response_info = info(task_number, **module_args).json()
    task_id = ""
    #old_state = ""
    
    if len(response_info["result"]) > 0:
       task_id = response_info["result"][0]["sys_id"]
       #old_state  = response_info["result"][0]["state"]

    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] + "/" + task_id
    data=module_args

    try:
        response = requests.post(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            #params=params,
            data=json.dumps(data),
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, task could not update: " + str(e)}

    return response

def validateOptions(module):

    if module.params["state"] == "present" or module.params["state"] == "create":
        return create(module.params["release"], **module.params)

    if module.params["state"] == "present" or module.params["state"] == "create":
        return create(**module.params)
    elif "" != module.params["task"] or module.params["state"] == "update":
        return update(module.params["release"], **module.params) 

def run_module():
    
    module_args = {
        "state": {
            "default": "present",
            "choices": ["present", "create"]
        },
        "sn_user": {"required": False, "type": "str"},
        "sn_pass": {"required": False, "type": "str", "no_log": True},
        "sn_base": {"required": True, "type": "str"},
        "sn_uri": {"required": False, "type": "str", "default": "/api/now/v2/table/rm_task"},
        "timeout": {"required": False, "type": "int", "default": 300},

        #For updating
        "task":{ "type": "str" },

        #For creating and updating
        "release":{ "type": "str" }, 
        "start_date":{ "type": "str" },
        "end_date":{ "type": "str" },
        "short_description":{ "type": "str" },
        "description":{ "type": "str" }, 
        "state_resolve":{ "type": "str" },
        "type":{ "type": "str" },
        "group":{ "type": "str" },
        "order":{ "type": "str" },
        "application":{ "type": "str" },
        "technology":{ "type": "str" },
        "version":{ "type": "str" },

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
            ('state', 'present', ('release', 'start_date', 'end_date', 'short_description', 'state_resolve', 'type', 'application' ,'group', 'description', 'technology', 'sn_user', 'sn_pass','sn_base'), False)
        ]   
    )

    if module.check_mode:
        module.exit_json(**result)
    else:
        response = validateOptions(module)

    result["message"] = json.loads(response.text)
    #result["message"] = json.loads(response.json())

    if response.status_code == 200 or response.status_code == 201:
        
        #Sólo consulta
        if module.params["state"] == "info" or module.params["state"] == "info_tasks":
            if len(response.json()['result']) > 0:
                result['message'] = response.json()["result"]
                result['changed'] = True
            else:
                result['message'] = "No records found!"
                result['changed'] = False
        #Aplica para otras acciones
        else:

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
        module.fail_json(msg="Response generic error: ",**result)

def main():
    run_module()

if __name__ == '__main__':
    main()