import pandas as pd
import ast

df = pd.read_csv('/home/isabella_gallego/Documentos/IC/incompletos.tsv', sep='\t')

# Ground truth
ground_truth_columns = ['Species name', 'Cultivar', 'Genotype', 'Treatment', 'Dev stage', 'Tissue', 'Age']

# Response evaluation
def evaluate_response(model_response, ground_truth):
    metrics = {
        "TP": 0,
        "FP": 0,
        "FN": 0
    }

    #  Comparison of keys and values - Ground truth/Model response
    for key in ground_truth:
        if key in model_response:
            if model_response[key] == ground_truth[key]:
                metrics["TP"] += 1  # True Positive
            else:
                metrics["FP"] += 1  # False Positive
        else:
            metrics["FN"] += 1  # False Negative

    for key in model_response:
        if key not in ground_truth:
            metrics["FP"] += 1

    return metrics

# Formatting 
def convert_to_dict(response):
    try:
        return ast.literal_eval(response)
    except:
        return {}

# Evaluation
results = []

for index, row in df.iterrows():
    ground_truth = {col: row[col] for col in ground_truth_columns}

    for model in ['Llama', 'Phi3', 'Gemma', 'GPT 3.5', 'GPT 4', 'GPT 4-o']:
        model_response = convert_to_dict(row[model])
        evaluation = evaluate_response(model_response, ground_truth)
        results.append({
            'PMID/SRA': row['PMID/ SRA'],
            'Model': model,
            'TP': evaluation['TP'],
            'FP': evaluation['FP'],
            'FN': evaluation['FN']
        })

results_df = pd.DataFrame(results)
results_df.to_excel('resultados_evaluacion_modelos.xlsx', index=False)

print("Evaluación completada y guardada en 'resultados_evaluacion_modelos.xlsx'")
