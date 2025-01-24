import requests

def create_pipefy_card(content):
    """
    Create a new card in Pipefy.

    Parameters:
        content (dict): A dictionary containing the API token, pipe ID, title, and fields.
            Required keys: 'api_token', 'pipe_id', 'title', 'fields'.

    Returns:
        dict: A dictionary with the created card's ID and title, or an error message.
    """
    import json

    # Extract variables from the content dictionary
    api_token = content.get('api_token')
    pipe_id = content.get('pipe_id')
    title = content.get('title')
    fields = content.get('fields')

    # GraphQL query for creating a card in Pipefy
    query = """
    mutation CreateCard($pipeId: ID!, $title: String!, $fields: [FieldValueInput]!) {
      createCard(input: {
        pipe_id: $pipeId,
        title: $title,
        fields_attributes: $fields
      }) {
        card {
          id
          title
        }
      }
    }
    """

    # Convert fields into the required format for the query
    fields_attributes = [
        {"field_id": key, "field_value": value} for key, value in fields.items()
    ]

    # Variables for the GraphQL mutation
    variables = {
        "pipeId": pipe_id,
        "title": title,
        "fields": fields_attributes
    }

    # Send the request to the Pipefy API
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.pipefy.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )

        # Debugging: Print the raw response for inspection
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)

        # Parse the response JSON
        if response.status_code == 200:
            data = response.json()
            card = data.get('data', {}).get('createCard', {}).get('card', {})
            return {
                "success": True,
                "card_id": card.get('id'),
                "card_title": card.get('title')
            }
        else:
            return {
                "success": False,
                "error": response.json()
            }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse response as JSON."
        }


# Example usage
content = {
    'api_token': 'eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3Mjg0ODQwNjQsImp0aSI6IjA4YjE0ZTUxLTNiZTUtNGZjZS04MTk2LWZmNDg1Mjk3MjY4NyIsInN1YiI6MzA1MTc2NDIzLCJ1c2VyIjp7ImlkIjozMDUxNzY0MjMsImVtYWlsIjoiYXJ0aHVyLnNvdXphQHByYXNvLmNvbS5iciJ9fQ.1OJ8H9Dn-RbdxWlnglRFqHpjDC6vzYWhSlZfX7bUNdHAUl6E7SqyAiPZhz9alOmEceXSGLIFf2jtdq726xdVLQ',
    'pipe_id': '305477886',
    'title': 'New Card Title',
    'fields': {
        "fornecedor": "Example Supplier",
        "data_do_agendamento": "2025-01-24",
        "hub": "HUB A",
        "cd": "CD 1",
        "centro_de_distribui_o": "Distribution Center X",
        "fornecedor_paletizado": "Yes",
        "se_sim_informe_a_quantidade_de_paletes": "5",
        "toneladas": "2",
        "exige_cobran_a_de_descarga": "No",
        "foi_agendado": "Yes",
        "observa_es_1": "No observations",
        "id": "12345"
    }
}

result = create_pipefy_card(content)

if result["success"]:
    print(f"Card created successfully! ID: {result['card_id']}, Title: {result['card_title']}")
else:
    print(f"Failed to create card: {result['error']}")
