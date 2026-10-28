from ai_agent.agent import ask_mechanic

response = ask_mechanic(
    "My check engine light is on. "
    "Check the available vehicle data and tell me "
    "what I should investigate first."
)

print("\nVirtual Garage AI Mechanic:\n")
print(response)