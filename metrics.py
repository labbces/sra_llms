def evaluate_response(model_response, ground_truth):
    metrics = {
        "TP": 0,
        "FP": 0,
        "TN": 0,
        "FN": 0
    }

    for key in ground_truth:
        if key in model_response:
            if model_response[key] == ground_truth[key]:
                metrics["TP"] += 1
            else:
                metrics["FP"] += 1
        else:
            metrics["FN"] += 1

    # Check for any extra keys not in ground truth
    for key in model_response:
        if key not in ground_truth:
            metrics["FP"] += 1

    return metrics
