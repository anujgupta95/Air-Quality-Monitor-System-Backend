import requests
import json

# Function to get healthcare instructions from Gemini API
def get_health_instructions_from_gemini(city, aqi, health_issues=None, api_key="your_gemini_api_key_here"):
    # Gemini API URL
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    # Prepare the prompt text
    user_input = f"City: {city}\nAQI: {aqi}\nHealth Condition: {health_issues if health_issues else 'None'}\n\nProvide personalized healthcare recommendations based on the AQI level and health condition."

    # Construct the payload according to the correct structure
    payload = {
        "contents": [{
            "parts": [{
                "text": user_input
            }]
        }]
    }

    # Set headers for the API request
    headers = {
        "Content-Type": "application/json"
    }

    # Send the request to the Gemini API
    response = requests.post(api_url, json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Directly extract the 'content' from the response
        content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "No personalized health instructions available.")
        return content
    else:
        raise ValueError(f"Error fetching content: {response.status_code} - {response.text}")

# Function to generate the markdown output
def generate_markdown_output(city, aqi, health_issues=None, api_key="your_gemini_api_key_here"):
    try:
        # Get health instructions from Gemini API
        health_instructions = get_health_instructions_from_gemini(city, aqi, health_issues, api_key)
        
        # Create the Markdown formatted string
        markdown_content = f"""
# AQI Health Advisory for {city}

**AQI Level**: {aqi}

### Healthcare Recommendations:

{health_instructions}

"""
        return markdown_content

    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
city = "Delhi"
aqi = 200
health_issues = "My surroundings are very bad and water in my area is also of very bad quality"  # Optional field, can be left as None


# # Generate the markdown output
# markdown_output = generate_markdown_output(city, aqi, health_issues, api_key)
# print(markdown_output)
