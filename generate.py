from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import time
import os
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
from multiprocessing import Process
import datasets

def save_code(name, code, lang):
  print(name, lang)
  if lang is None:
    file = os.path.join('render', name)
  else:
    file = os.path.join('render', lang, name)
    
  with open(file, "w") as fp:
    fp.write(code)
    
  fp.close()
  
def web_server():
  httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
  httpd.serve_forever()

def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)
    
# start web server
webserver = Process(target=web_server)
webserver.start()

# create render directory
if not os.path.exists('render'):
  os.makedirs('render')
  
if not os.path.exists('render/es'):
  os.makedirs('render/es')
  
if not os.path.exists('render/en'):
  os.makedirs('render/en')  


datasets.render()
exit()

# start selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(chrome_options)

# render index.html
#driver.get(f"http://localhost:8000")
#time.sleep(1)
#code = driver.page_source
#save_code('index.html', code, None)
shutil.copy('index.html', 'render/index.html')  
  
# render rest of html pages
files = [f for f in os.listdir('es') if '.html' in f and f != 'index.html']
for lang in ['es', 'en']:

  for file in files:
    print(f"Rendering {file}")
    driver.get(f"http://localhost:8000/es/{file}?lang={lang}&render=1")
    time.sleep(1)
    code = driver.page_source
    save_code(file, code, lang)
  
# copy static files
copy_and_overwrite('files', f'render/files')
copy_and_overwrite('images', f'render/images')

# stop web server
webserver.terminate()
