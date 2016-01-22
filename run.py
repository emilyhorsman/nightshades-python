# Find me in nightshades/http/__init__.py!
import nightshades
from nightshades.http import app

if __name__ == '__main__':
    nightshades.load_dotenv()
    app.run()
