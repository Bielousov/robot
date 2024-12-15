import os
from numpy import load, save

def loadModel(model, path):
  try:
    modelData = load(path, allow_pickle=True).tolist()
    model.accuracy = modelData['accuracy']
    model.baseAccuracy = modelData['accuracy']
    model.epoch = modelData['epoch']
    model.baseEpoch = modelData['epoch']
    model.inputs = modelData['inputs']
    model.layers = modelData['layers']
    model.outputs = modelData['outputs']
    print('Loaded model from', path)
  except FileNotFoundError: 
    print("Model not found at", path)
  except:
    print("Could not load the model from", path)

def saveModel(model, path):
  try:
    modelData = {
      'accuracy': model.accuracy,
      'epoch': model.epoch,
      'inputs': model.inputs,
      'layers': model.layers,
      'outputs': model.outputs,
    }
    save(path, modelData, allow_pickle = True)
    print("Model saved to", path, os.stat(path).st_size, "bytes")
  except:
    print("Could not save the model to", path)
    