import nightshades

if __name__ == '__main__':
    nightshades.load_dotenv()

    # Find me in nightshades/http/__init__.py!
    from nightshades.http import app
    app.run(host = '0.0.0.0')
