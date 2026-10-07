def schedule_tasks(llms, tasks, lam, times):
    return [{"llm": llm.name, "task": tasks[0].name} for llm in llms]
