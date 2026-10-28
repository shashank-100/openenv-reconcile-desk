from openenv.core.env_server.http_server import create_app
from .environment import ReconcileEnvironment
from .models import Tbench2Action,Tbench2Observation
app=create_app(ReconcileEnvironment,Tbench2Action,Tbench2Observation,env_name='reconcile_desk',max_concurrent_envs=8)
