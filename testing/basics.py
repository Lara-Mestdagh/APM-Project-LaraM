import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login Page")
        self.geometry("400x300")  # Adjust the size to accommodate the new elements

        # Username label and text entry box
        self.label_username = customtkinter.CTkLabel(self, text="Username:")
        self.label_username.pack(pady=(20, 0))  # Add some vertical padding
        self.entry_username = customtkinter.CTkEntry(self, width=200, placeholder_text="Enter username")
        self.entry_username.pack()

        # Password label and password entry box
        self.label_password = customtkinter.CTkLabel(self, text="Password:")
        self.label_password.pack(pady=(10, 0))  # Add some vertical padding
        self.entry_password = customtkinter.CTkEntry(self, width=200, placeholder_text="Enter password", show="*")
        self.entry_password.pack()

        # Login button
        self.button_login = customtkinter.CTkButton(self, text="Login", command=self.login_callback)
        self.button_login.pack(pady=(20, 10))  # Add some vertical padding

        # Register button
        self.button_register = customtkinter.CTkButton(self, text="Register", command=self.register_callback)
        self.button_register.pack()

    def login_callback(self):
        # For now, just print a message; later, handle login logic
        print("Login button clicked")
        print("Username:", self.entry_username.get())
        print("Password:", self.entry_password.get())

    def register_callback(self):
        # For now, just print a message; later, handle registration logic
        print("Register button clicked")

app = App()
app.mainloop()
