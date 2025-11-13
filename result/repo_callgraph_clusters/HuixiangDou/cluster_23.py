# Cluster 23

@app.on_event('startup')
def on_startup():
    start_scheduler()

@app.on_event('shutdown')
def on_shutdown():
    stop_scheduler()

