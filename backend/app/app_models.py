from app.ai_models import ai_model_base, \
  default_model, \
  message_model, \
  assistant_model, \
  assistant_model2, \
  researcher_model, \
  hi_model

class AppModels:
  def __init__(self, app):
    self.app = app
    self.models = ai_model_base.AIModels()
    self.models.add_model(default_model.DefaultModel('chat', app.llm, app), default=True)
    self.models.add_model(assistant_model.AssistantModel('assistant-orig', app.llm, app))
    self.models.add_model(assistant_model2.AssistantModel('assistant', app.llm, app))
    self.models.add_model(message_model.MessageModel('message', app.llm, app))
    self.models.add_model(researcher_model.ResearcherModel('researcher', app.llm, app))
    self.models.add_model(hi_model.HiModel('hi', app.llm, app))
    self.model_list = self.models.models

  def get_model(self, name):
    return self.models.get_model(name)