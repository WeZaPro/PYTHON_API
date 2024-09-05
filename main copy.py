from flask import Flask, render_template

app = Flask(__name__)

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == '__main__':
  app.run(port=5000)
