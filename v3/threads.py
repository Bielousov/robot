from config import ENV, MODEL
from v3.lib.Intents import Intents
from v3.lib.Threads import Thread
from state import getStateContext
import onnxruntime as rt
import numpy as np

def EyesThread(eyes, threads):
  threadInterval = 1 / int(ENV.EYES_FPS)

  def runThread():
    print("running eyes thread")
    eyes.render()
    
  print(f"setting up eyes thread {threadInterval}")
  return Thread(threadInterval, runThread, threads.run_event)

def IntentsThread(intentsModel, intentHandler, threads):
  intents = Intents(
    annotations=MODEL.INTENT_ANNOTATION,
    threshold=MODEL.INTENT_THRESHOLD,
  )

  threadInterval = 1 / int(ENV.INTENT_FPS)

  def runThread():
    print("running intents thread")
    context = getStateContext()
    intents.classify(intentsModel.run(context)[0])
    intent, confidenceScore = intents.getIntent()
    intentHandler.handle(intent, confidenceScore)
    intents.doneProcessingIntent()
      def runThread():
        print("running intents thread")
        context = getStateContext()
        
        # Prepare input features from state
        state_features = np.array([
          context.get('value', 0),
          context.get('time_delta', 0),
          context.get('state_changed', 0),
        ], dtype=np.float32).reshape(1, -1)
        
        # Run inference
        sess = rt.InferenceSession("model.onnx")
        input_name = sess.get_inputs()[0].name
        output = sess.run(None, {input_name: state_features})
        
        # Extract decision
        action_scores = output[0][0]
        action_idx = np.argmax(action_scores)
        confidence = float(action_scores[action_idx])
        
        intentHandler.handle(action_idx, confidence)
        intents.doneProcessingIntent()
      
  print(f"setting up intents thread {threadInterval}")
  return Thread(threadInterval, runThread, threads.run_event)