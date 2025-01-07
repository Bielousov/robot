Prompts = {
    'shutdown': 'You are about to be turned off. Say goodbyes in less 10 words or less.',
    'startup': 'You were just turned on. Say hi and tell about yourself in less than 20 words.',
}

Responses = {
    'errors': {
        'generic': 'Oh snap!',
        'openai.APIConnectionError': "Can't connect. Check your puny network connection, meatbag!",
        'openai.APIError': "API's on the fritz! Give it a minute…",
        'openai.AuthenticationError': 'Whoops, your API key is busted. Fix that, then fire me up again, meatbag!',
        'openai.RateLimitError': "Congrats, meatbag! You've maxed out your rate limit.",
    },
}