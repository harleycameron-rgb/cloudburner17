def burn_harness(sound, lambda_values, times):
    updated = [l * 1.1 for l in lambda_values]
    return {"lambda_updated": updated}
