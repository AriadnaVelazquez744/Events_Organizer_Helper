import requests
from bs4 import BeautifulSoup
import json

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

url = "https://www.springworks.in/blog/us-holiday-calendar/"
resp = requests.get(url, headers=headers)

resp.raise_for_status()  # ahora no debería dar error 403

soup = BeautifulSoup(resp.text, "html.parser")
print(soup.title.string)


# Localizar los encabezados
fed_h2 = soup.find("h2", string=lambda t: t and "Federal holidays" in t)
nonfed_h2 = soup.find("h2", string=lambda t: t and "Non-federal holidays" in t)

def extract_list(h2_element):
    items = []
    for sib in h2_element.find_next_siblings():
        if sib.name == "h2":
            break
        if sib.name in ("p", "ul"):
            text = sib.get_text(separator="\n").strip()
            for line in text.splitlines():
                # omitir líneas vacías
                line = line.strip()
                if line:
                    # separar nombre y fecha
                    items.append(line)
    return items

federal = extract_list(fed_h2)
non_federal = extract_list(nonfed_h2)

# Formatear: separar nombre y fecha
from dateutil import parser
def split_name_date(item):
    # formato: "Name: Month Day, Year (weekday)"
    if ":" in item:
        name, rest = item.split(":", 1)
        date_str = rest.split("(")[0].strip()
        try:
            dt = parser.parse(date_str)
            iso = dt.date().isoformat()
        except:
            iso = date_str
        return {"name": name.strip(), "date": iso}
    else:
        # otros formatos, dejar entero
        return {"text": item}

fed_list = [split_name_date(i) for i in federal]
nonfed_list = [split_name_date(i) for i in non_federal]

output = {"federal": fed_list, "non_federal": nonfed_list}

print(json.dumps(output, indent=2, ensure_ascii=False))
