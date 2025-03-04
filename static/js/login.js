import React, { useState } from "react";
import ReactDOM from "react-dom";

const Login = () => {
  const [formData, setFormData] = useState({ username: "", password: "" });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl font-bold text-center mb-4">Login</h2>
        <form method="POST">
          <input type="hidden" name="csrfmiddlewaretoken" value={window.CSRF_TOKEN} />
          <div className="mb-4">
            <label className="block text-gray-700">Username</label>
            <input
              type="text"
              name="username"
              className="w-full p-2 border rounded"
              required
              onChange={handleChange}
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Password</label>
            <input
              type="password"
              name="password"
              className="w-full p-2 border rounded"
              required
              onChange={handleChange}
            />
          </div>
          <button type="submit" className="w-full bg-green-500 text-white p-2 rounded">
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

ReactDOM.render(<Login />, document.getElementById("react-login"));