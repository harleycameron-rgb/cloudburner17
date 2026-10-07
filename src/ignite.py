if __package__:
    from .harmony import unify_lambdas
else:
    from harmony import unify_lambdas


def ignite(sound, lambda_values, times):
    return {
        "InvariantEngine": {
            "sound": sound,
            "lambda": unify_lambdas(lambda_values),
            "times": times
        }
    }
