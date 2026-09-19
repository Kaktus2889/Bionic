from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url:str="postgresql+psycopg://aicompany:change-me@localhost:5432/aicompany"
    redis_url:str="redis://localhost:6379/0"
    cors_origins:str="http://localhost:3000"
    max_actions_per_tick:int=20
    max_messages_per_tick:int=30
    max_llm_calls_per_tick:int=10
    daily_token_budget:int=200000
    daily_cost_budget:float=20.0
    llm_provider:str="deterministic"
    llm_endpoint:str=""
    llm_api_key:str=""
    llm_model:str="strong"
    llm_cheap_model:str="cheap"
    company_review_interval:int=5
    max_plan_steps:int=6
    cycle_lock_ttl:int=60
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
