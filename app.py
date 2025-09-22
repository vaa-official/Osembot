from chatbot.api import app 
from config import Config
app.secret_key = getattr(app, 'secret_key', Config.SECRET_KEY)

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=Config.PORT)
