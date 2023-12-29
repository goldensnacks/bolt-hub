import requests
from bs4 import BeautifulSoup

# Define the URL of the website you want to scrape
url = "https://www.worldgovernmentbonds.com/country/japan/"  # Replace with the URL of the website you want to scrape

# Send an HTTP GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the HTML elements that contain the article titles
    # You will need to inspect the website's HTML structure to find the right elements
    article_elements = soup.find_all("h2")  # Replace "h2" with the appropriate HTML tag

    # Loop through the article elements and extract the titles
    for article in article_elements:
        title = article.text.strip()  # Get the text content and remove leading/trailing spaces
        print(article)
else:
    print("Failed to retrieve the webpage. Status code:", response.status_code)
