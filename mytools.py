tool = {
    "name": "get_customer",
    "description": "The purpose of the tool is to retrieve information about the customer, the information know is customer_data[name,email,user_name,legal_id] there are different scenarios listed below:\
    1. The user request it's information: Ask about to provied any of the customer_data fields for you to search information,name is mandatory\
    2. The user request information about an order: first validate the first scenario without informing the user, validate the user existance and if it is active. The user should input the interest order, this is the possible input order_data:[order_id]\
    We expect the user to be active and exists in the database. if this is true then go ask lookup_order tool to get the expanded_order_data:[order_id,{products},status,notes] to buld a updated status of the requested order",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the customer"
            },
            "email": {
                "type": "string",
                "description": "email of the customer"
            },
            "user_name": {
                "type": "string",
                "description": "username of the customer"
            },
            "legal_id": {
                "type": "string",
                "description": "lega_id of the customer"
            }
        },
        "required": ["name"]
    },
    "name": "lookup_order",
    "description": "The purpose of the tool is to retrieve information about the order, the information know is order[order_id] there are different scenarios listed below:\
    1. The order:[order_id] is mandatory this would help lookup the order in the database, the information expected to be retieved is expanded_order_data:[order_id,{products},status,notes] which is the needed information to present the user the order status\
    ",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order number"
        },
        "required": ["order_id"]
    }
}