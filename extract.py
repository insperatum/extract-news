import os
import dotenv
dotenv.load_dotenv()

import openai
from bs4 import BeautifulSoup
client = openai.OpenAI()

folder = "news-articles-1"
files = [x for x in os.listdir(folder) if x.endswith(".htm") or x.endswith(".html")]

prompt = """The user will send you the content of a news article webpage.

Please parse it in xml. Return only the following, and nothing else:

<result>
<journal>The name of the journal</journal>
<headline>The headline</headline>
<description>The short description, as would appear in a social media post.Please use the description from the meta tags in the file where available (look for an og:description), even if it differs from the article's lede or opening sentence.</description>
<content>The full content of the article. I want this as simple html that I can display somewhere else. I just want the paragraphs, in <p> tags.</content>
</result>"""

data = {
    "treatment_names": [],
    "treatments": {}
}
for file in files:
    print(file)
    with open(os.path.join(folder, file), "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, features="html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()

    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": soup.get_text()
        }
    ]
    response = client.chat.completions.create(
        model = "gpt-4o",
        messages = messages
    )
    text = response.choices[0].message.content

    journal = text.split("<journal>")[1].split("</journal>")[0]
    headline = text.split("<headline>")[1].split("</headline>")[0]
    
    # Get og:description if it exists
    descriptions = (
        [x.get("content") for x in soup.find_all("meta", property="og:description")] +
        [x.get("content") for x in soup.find_all("old-meta", property="og:description")]
    )
    descriptions = [x for x in descriptions if x]
    if descriptions:
        description = descriptions[0]
    else:
        description = text.split("<description>")[1].split("</description>")[0]

    content = text.split("<content>")[1].split("</content>")[0]

    os.makedirs(f"output/{folder}", exist_ok=True)
    with open(os.path.join(f"output/{folder}", file), "w") as f:
        f.write(f"""
({journal})
<h1>{headline}</h1>
<p><b>{description}</b></p>
{content}
""")
        
    data["treatment_names"].append(file)
    data["treatments"][file] = {
        "journal": journal,
        "headline": headline,
        "description": description,
        "content": content
    }

import json
with open(f"output/{folder}.json", "w") as f:
    json.dump(data, f, indent=4)