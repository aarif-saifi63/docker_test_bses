import { useState, useRef, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import { AuthContext } from "../context/AuthContext";
import Img from "../assets/Img.jpg";
export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [captchaInput, setCaptchaInput] = useState("");
  const [captchaCode, setCaptchaCode] = useState("");
  const canvasRef = useRef(null);

  const { login } = useContext(AuthContext);

  const generateCaptcha = () => {
    const num1 = Math.floor(Math.random() * 20) + 1;
    const num2 = Math.floor(Math.random() * 20) + 1;


    const answer = num1 + num2;

    // Store the answer as a string for validation
    setCaptchaCode(answer.toString());

    // Draw on canvas
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font = "25px Georgia";
      ctx.strokeText(`${num1} + ${num2} = ?`, 10, 30);
    }
  };

  useEffect(() => {
    generateCaptcha();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validate CAPTCHA first
    if (captchaInput !== captchaCode) {
      setError("Invalid Captcha. Please try again.");
      setEmail("");
      setPassword("");
      setCaptchaInput("");
      generateCaptcha();
      return;
    }

    setLoading(true);

    try {
      const res = await login(email, password);

      if (res.success) {
        navigate("/");
      } else {
        setError(res.message || "Invalid credentials");
        setCaptchaInput("");
        generateCaptcha();
      }
    } catch (err) {
      setError(err.message || "An error occurred. Please try again.");
      setCaptchaInput("");
      generateCaptcha();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center bg-white p-8">
        <img src={logo} alt="BSES" className="mb-6 h-12" />
        <h2 className="text-2xl font-bold mb-6">Sign in to your account</h2>

        <form onSubmit={handleSubmit} className="w-full max-w-md">
          {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-4 text-sm">{error}</div>}

          <label className="block text-sm text-gray-600 mb-1">Email id</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="alexsmit@gmail.com"
            className="w-full border p-3 rounded mb-4"
            required
          />

          <label className="block text-sm text-gray-600 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="***********"
            className="w-full border p-3 rounded mb-4"
            required
          />

          {/* CAPTCHA Section */}
          <div className="mb-4">
            <label className="block text-sm text-gray-600 mb-1">Enter Captcha</label>
            <div className="flex items-center gap-3">
              <canvas
                ref={canvasRef}
                width="150"
                height="50"
                className="border rounded"
              />
              <button
                type="button"
                onClick={generateCaptcha}
                className="px-3 py-2 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                ↻
              </button>
            </div>
            <input
              type="text"
              value={captchaInput}
              onChange={(e) => setCaptchaInput(e.target.value)}
              placeholder="Enter the answer"
              className="w-full border p-3 rounded mt-2"
              required
            />
          </div>

          {/* <div className="text-right text-sm mb-4">
              <button type="button" className="text-gray-500 hover:underline">
                Forgot Password ?
              </button>
            </div> */}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 text-white py-3 rounded hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>

      {/* Right */}
      <div className="hidden lg:flex w-1/2 bg-red-700 text-white flex-col justify-center items-center">
        <h1 className="text-4xl font-bold mb-6 text-center px-8 leading-tight">
          POWERING DELHI AND EMPOWERING CONSUMERS
        </h1>
        <img src={Img} alt="admin" className="rounded-lg shadow-lg max-w-full" />
      </div>
    </div>
  );
}