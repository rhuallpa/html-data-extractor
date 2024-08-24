import os
from flask import Flask, request, render_template, redirect, url_for
from bs4 import BeautifulSoup
import pandas as pd
from werkzeug.utils import secure_filename
from difflib import get_close_matches

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'htm', 'html'}

# Lista de objetos analizados relevantes
RELEVANT_OBJECTS = [
    "Viscosidad de la Sangre", "Cristal de Colesterol", "Grasa en Sangre", 
    "Resistencia Vascular", "Elasticidad Vascular", "Demanda de Sangre Miocardial", 
    "Volumen de Perfusión Sanguínea Miocardial", "Consumo de Oxígeno Miocardial", 
    "Volumen de Latido", "Impedancia Ventricular Izquierda de Expulsión", 
    "Fuerza de Bombeo Efectiva Ventricular Izquierda", "Elasticidad de Arteria Coronaria", 
    "Presión de Perfusión Coronaria", "Elasticidad de Vaso Sanguíneo Cerebral", 
    "Estado de Suministro Sanguíneo de Tejido Cerebral", "Coeficiente de Secreción de Pepsina", 
    "Coeficiente de Función de Peristalsis Gástrica", "Coeficiente de Función de Absorción Gástrica", 
    "Coeficiente de Función de Peristalsis del Intestino Delgado", 
    "Coeficiente de Función de Absorción del Intestino Delgado", 
    "Coeficiente de la Función de Peristalsis del Intestino Grueso (colon)", 
    "Coeficiente de absorción colónica", "Coeficiente intestinal bacteriano", 
    "Coeficiente de presión intraluminal", "Metabolismo de las proteínas", 
    "Función de producción de energía", "Función de Desintoxicación", 
    "Función de Secreción de Bilis", "Contenido de Grasa en el Hígado", 
    "Seroglobulina (A/G)", "Bilirrubina Total (TBIL)", "Fosfatasa Alcalina (ALP)", 
    "Ácidos Biliares Totales Séricos (TBA)", "Bilirrubina (DBIL)", "Insulina", 
    "Polipéptido Pancreático (PP)", "Glucagón", "Índice de Urobilinógeno", 
    "Índice de Ácido Úrico", "Índice de Nitrógeno Ureico en la Sangre (BUN)", 
    "Índice de Proteinuria", "Capacidad Vital (VC)", "Capacidad Pulmonar Total (TLC)", 
    "Resistencia de las Vías Aéreas (RAM)", "Contenido de Oxígeno Arterial (PaCO2)", 
    "Estado del Suministro Sanguíneo al Tejido Cerebral", "Arterioesclerosis Cerebral", 
    "Estado Funcional de Nervio Craneal", "Índice de Emoción", "Índice de Memoria (ZS)", 
    "Calcio", "Hierro", "Zinc", "Selenio", "Fósforo", "Potasio", "Magnesio", 
    "Cobre", "Cobalto", "Manganeso", "Yodo", "Níquel", "Flúor", "Molibdeno", 
    "Vanadio", "Estaño", "Silicio", "Estroncio", "Boro"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_data_from_html(html_path):
    with open(html_path, 'r', encoding='iso-8859-1') as file:
        soup = BeautifulSoup(file, 'html.parser')
        tables = soup.find_all('table')
        
        data = []
        for table in tables:
            rows = table.find_all('tr')[1:]  # Omitir la fila del encabezado
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    objeto_analizado = ' '.join(cols[0].text.split()).strip().lower()  # Normalización del texto
                    valor_obtenido = cols[2].text.strip()

                    # Verificar coincidencia exacta o aproximada
                    matches = get_close_matches(objeto_analizado, [obj.lower() for obj in RELEVANT_OBJECTS], n=1, cutoff=0.8)
                    if matches and valor_obtenido:
                        # Usar el nombre exacto del parámetro de la lista RELEVANT_OBJECTS
                        original_match = RELEVANT_OBJECTS[[obj.lower() for obj in RELEVANT_OBJECTS].index(matches[0])]
                        data.append([original_match, valor_obtenido])
        
        # Crear DataFrame y filtrar solo los parámetros relevantes
        df = pd.DataFrame(data, columns=['Objeto Analizado', 'Valor Obtenido'])
        df = df[df['Objeto Analizado'].isin(RELEVANT_OBJECTS)]
        df = df.drop_duplicates(subset='Objeto Analizado', keep='first')
        df.reset_index(drop=True, inplace=True)  # Resetear índice para asegurar consecutividad
        df.index += 1  # Asegurar que el índice comience en 1
        return df

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'html' not in request.files:
            return redirect(request.url)
        file = request.files['html']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            df = extract_data_from_html(file_path)
            df.reset_index(drop=True, inplace=True)
            df.index += 1  # Asegura que la numeración esté bien ajustada
            return render_template('index.html', tables=[df.to_html(classes='table table-striped table-bordered', header="true", index=True)], file_name=filename)
    
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('objeto_analizado')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.listdir(app.config['UPLOAD_FOLDER'])[0])  # Suponiendo que solo hay un archivo cargado

    df = extract_data_from_html(file_path)
    df.reset_index(drop=True, inplace=True)
    df.index += 1  # Asegura que la numeración esté bien ajustada

    # Buscar coincidencia aproximada con el término de búsqueda
    matches = get_close_matches(query.lower(), [obj.lower() for obj in RELEVANT_OBJECTS], n=1, cutoff=0.8)
    if matches:
        filtered_df = df[df['Objeto Analizado'].str.lower() == matches[0]]
    else:
        filtered_df = pd.DataFrame(columns=['Objeto Analizado', 'Valor Obtenido'])  # DataFrame vacío si no hay coincidencia
    
    return render_template('index.html', tables=[filtered_df.to_html(classes='table table-striped table-bordered', header="true", index=True)], file_name=os.path.basename(file_path))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
