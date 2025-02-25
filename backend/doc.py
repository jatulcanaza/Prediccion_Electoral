# Importar las bibliotecas necesarias
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
import pandas as pd
import re

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Inicializar la aplicación Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicializar el cliente de Groq
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise ValueError("Falta la API Key de Groq en el archivo .env")
qclient = Groq(api_key=api_key)

# Variables globales para almacenar los datos procesados
votos_luisa = 0
votos_noboa = 0
votos_nulo = 0
conclusion = ""

# Ruta para manejar la subida de archivos y generar un resumen
@app.route('/summarize-file', methods=['POST'])
def summarize_file():
    global votos_luisa, votos_noboa, votos_nulo, conclusion

    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se proporcionó ningún archivo"}), 400

        file = request.files['file']
        file_extension = file.filename.split('.')[-1].lower()

        num_rows = int(request.form.get('num_rows', 1000))

        if file_extension == 'xlsx':
            df = pd.read_excel(file)
            
            if 'text' not in df.columns:
                return jsonify({"error": "El archivo no contiene la columna 'text'"}), 400
            
            df_text = df[['text']]
            
            if num_rows > len(df_text):
                num_rows = len(df_text)
            
            random_rows = df_text.sample(n=num_rows)
            text = random_rows.to_string(index=False)
        else:
            return jsonify({"error": "Formato de archivo no soportado"}), 400

        if not text.strip():
            return jsonify({"error": "No se pudo extraer texto del archivo"}), 400

        votos_luisa = text.lower().count("luisa")
        votos_noboa = text.lower().count("noboa")
        votos_nulo = text.lower().count("nulo")

        prompt = (
            "A continuación te proporciono una lista de comentarios. "
            "Por favor, identifica y cuenta cuántos de estos comentarios son votos para Luisa, Noboa o votos nulos. Agrega una conclusión una vez contado los votos. "
            "Devuelve solo los conteos en el siguiente formato: "
            "Votos Luisa: X, Votos de Noboa: Y, Votos Nulo: Z. Conclusión: A "
            "Aquí está la lista de comentarios:\n\n" + text[:3000]
        )

        response = qclient.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un asistente que identifica votos en comentarios y devuelve los resultados en un formato específico."},
                {"role": "user", "content": prompt},
            ],
            model="mixtral-8x7b-32768"
        )

        summary = response.choices[0].message.content

        votos_luisa_match = re.search(r'Votos\s*Luisa:\s*(\d+)', summary)
        votos_noboa_match = re.search(r'Votos\s*de\s*Noboa:\s*(\d+)', summary)
        votos_nulo_match = re.search(r'Votos\s*Nulo:\s*(\d+)', summary)

        if votos_luisa_match and votos_noboa_match and votos_nulo_match:
            votos_luisa = int(votos_luisa_match.group(1))
            votos_noboa = int(votos_noboa_match.group(1))
            votos_nulo = int(votos_nulo_match.group(1))
        else:
            print("⚠️ Groq no devolvió el formato esperado. Usando conteos manuales.")

        conclusion_match = re.search(r'Conclusión:(.*)', summary, re.DOTALL)
        conclusion = conclusion_match.group(1).strip() if conclusion_match else "No se pudo generar una conclusión."

        return jsonify({
            "votos_luisa": votos_luisa,
            "votos_noboa": votos_noboa,
            "votos_nulo": votos_nulo,
            "conclusion": conclusion
        })

    except Exception as e:
        print(f"❌ Error en el servidor: {e}")
        return jsonify({"error": str(e)}), 500

# Ruta para manejar las preguntas del chatbot
@app.route('/ask-question', methods=['POST'])
def ask_question():
    global votos_luisa, votos_noboa, votos_nulo, conclusion

    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "No se proporcionó ninguna pregunta"}), 400

        # Crear un contexto con los datos procesados
        context = f"""
        Aquí tienes un resumen de los datos analizados:
        - Votos Luisa: {votos_luisa}
        - Votos Noboa: {votos_noboa}
        - Votos Nulo: {votos_nulo}
        - Conclusión: {conclusion}
        """

        # Combinar el contexto con la pregunta del usuario
        prompt = f"{context}\n\nPregunta: {question}\n\nRespuesta:"

        # Enviar la pregunta al modelo de lenguaje
        response = qclient.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un asistente que responde preguntas basadas en los datos proporcionados."},
                {"role": "user", "content": prompt},
            ],
            model="mixtral-8x7b-32768"
        )

        answer = response.choices[0].message.content

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"❌ Error en el servidor: {e}")
        return jsonify({"error": str(e)}), 500

# Inicia el servidor Flask
if __name__ == '__main__':
    app.run(debug=True, port=5000)