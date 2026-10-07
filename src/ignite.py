def ignite(sound, lambda_values, times):
    return {
        "InvariantEngine": {
            "sound": sound,
            "lambda": lambda_values,
            "times": times
        }
    }
