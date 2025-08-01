import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Mail, Lock, User, Phone, Building, Briefcase, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { authAPI } from '../services/api';

const AuthPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(null);

  // Form data
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    department: '',
    job_title: '',
    remember_me: false
  });

  // Real-time password strength validation
  useEffect(() => {
    if (!isLogin && formData.password) {
      validatePasswordStrength(formData.password);
    }
  }, [formData.password, isLogin]);

  const validatePasswordStrength = (password) => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    const score = Object.values(checks).filter(Boolean).length;
    const strength = score < 3 ? 'weak' : score < 5 ? 'medium' : 'strong';

    setPasswordStrength({
      score,
      strength,
      checks,
      isValid: score >= 4
    });
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear field-specific errors
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (!isLogin && (!passwordStrength || !passwordStrength.isValid)) {
      newErrors.password = 'Password does not meet security requirements';
    }

    // Registration-specific validation
    if (!isLogin) {
      if (!formData.first_name) {
        newErrors.first_name = 'First name is required';
      } else if (!/^[a-zA-Z\s\-'\.]+$/.test(formData.first_name)) {
        newErrors.first_name = 'First name contains invalid characters';
      }

      if (!formData.last_name) {
        newErrors.last_name = 'Last name is required';
      } else if (!/^[a-zA-Z\s\-'\.]+$/.test(formData.last_name)) {
        newErrors.last_name = 'Last name contains invalid characters';
      }

      if (formData.phone && !/^[\+]?[1-9][\d]{0,15}$/.test(formData.phone.replace(/[\s\-\(\)]/g, ''))) {
        newErrors.phone = 'Please enter a valid phone number';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});
    setSuccess('');

    try {
      if (isLogin) {
        // Login
        const response = await authAPI.login({
          email: formData.email,
          password: formData.password,
          remember_me: formData.remember_me
        });

        if (response.success) {
          setSuccess('Login successful! Redirecting...');
          
          // Store tokens
          localStorage.setItem('access_token', response.data.tokens.access_token);
          localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
          localStorage.setItem('user', JSON.stringify(response.data.user));

          // Call onLogin callback
          setTimeout(() => {
            onLogin(response.data.user, response.data.tokens);
          }, 1000);
        } else {
          setErrors({ general: response.error || 'Login failed' });
        }
      } else {
        // Registration
        const registrationData = {
          email: formData.email,
          password: formData.password,
          first_name: formData.first_name,
          last_name: formData.last_name
        };

        // Add optional fields if provided
        if (formData.phone) registrationData.phone = formData.phone;
        if (formData.department) registrationData.department = formData.department;
        if (formData.job_title) registrationData.job_title = formData.job_title;

        const response = await authAPI.register(registrationData);

        if (response.success) {
          setSuccess('Registration successful! Please check your email for verification.');
          
          // Switch to login form after successful registration
          setTimeout(() => {
            setIsLogin(true);
            setFormData(prev => ({
              ...prev,
              password: '',
              first_name: '',
              last_name: '',
              phone: '',
              department: '',
              job_title: ''
            }));
          }, 2000);
        } else {
          if (response.data && response.data.issues) {
            // Handle validation errors from backend
            const backendErrors = {};
            response.data.issues.forEach(issue => {
              if (issue.includes('email')) backendErrors.email = issue;
              else if (issue.includes('password')) backendErrors.password = issue;
              else if (issue.includes('name')) backendErrors.first_name = issue;
              else backendErrors.general = issue;
            });
            setErrors(backendErrors);
          } else {
            setErrors({ general: response.error || 'Registration failed' });
          }
        }
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setErrors({ general: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setErrors({});

    try {
      // Try to register a demo user first, then login
      const demoUser = {
        email: 'demo@enterprise-ai.com',
        password: 'DemoPassword123!',
        first_name: 'Demo',
        last_name: 'User',
        department: 'Technology',
        job_title: 'System Administrator'
      };

      // Try registration (will fail if user exists, which is fine)
      await authAPI.register(demoUser);

      // Now login with demo credentials
      const response = await authAPI.login({
        email: demoUser.email,
        password: demoUser.password,
        remember_me: false
      });

      if (response.success) {
        setSuccess('Demo login successful! Redirecting...');
        
        // Store tokens
        localStorage.setItem('access_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));

        // Call onLogin callback
        setTimeout(() => {
          onLogin(response.data.user, response.data.tokens);
        }, 1000);
      } else {
        setErrors({ general: 'Demo login failed. Please try manual login.' });
      }
    } catch (error) {
      console.error('Demo login error:', error);
      setErrors({ general: 'Demo login failed. Please try manual login.' });
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrengthColor = () => {
    if (!passwordStrength) return 'bg-gray-200';
    switch (passwordStrength.strength) {
      case 'weak': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'strong': return 'bg-green-500';
      default: return 'bg-gray-200';
    }
  };

  const getPasswordStrengthWidth = () => {
    if (!passwordStrength) return '0%';
    return `${(passwordStrength.score / 5) * 100}%`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center mb-4">
            <Building className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Enterprise AI System</h1>
          <p className="text-gray-600">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
            <span className="text-green-800">{success}</span>
          </div>
        )}

        {/* Error Message */}
        {errors.general && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
            <span className="text-red-800">{errors.general}</span>
          </div>
        )}

        {/* Auth Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.email ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter your email"
                  disabled={loading}
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Registration Fields */}
            {!isLogin && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  {/* First Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleInputChange}
                        className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                          errors.first_name ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="First name"
                        disabled={loading}
                      />
                    </div>
                    {errors.first_name && (
                      <p className="mt-1 text-sm text-red-600">{errors.first_name}</p>
                    )}
                  </div>

                  {/* Last Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        errors.last_name ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="Last name"
                      disabled={loading}
                    />
                    {errors.last_name && (
                      <p className="mt-1 text-sm text-red-600">{errors.last_name}</p>
                    )}
                  </div>
                </div>

                {/* Phone (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number <span className="text-gray-400">(Optional)</span>
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        errors.phone ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="+1 (555) 123-4567"
                      disabled={loading}
                    />
                  </div>
                  {errors.phone && (
                    <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Department (Optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Department <span className="text-gray-400">(Optional)</span>
                    </label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={handleInputChange}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Engineering"
                        disabled={loading}
                      />
                    </div>
                  </div>

                  {/* Job Title (Optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Title <span className="text-gray-400">(Optional)</span>
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        name="job_title"
                        value={formData.job_title}
                        onChange={handleInputChange}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Software Engineer"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.password ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter your password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}

              {/* Password Strength Indicator (Registration only) */}
              {!isLogin && formData.password && (
                <div className="mt-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Password Strength</span>
                    <span className={`font-medium ${
                      passwordStrength?.strength === 'strong' ? 'text-green-600' :
                      passwordStrength?.strength === 'medium' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {passwordStrength?.strength?.toUpperCase()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                      style={{ width: getPasswordStrengthWidth() }}
                    ></div>
                  </div>
                  {passwordStrength && (
                    <div className="mt-2 text-xs text-gray-600">
                      <div className="grid grid-cols-2 gap-1">
                        <span className={passwordStrength.checks.length ? 'text-green-600' : 'text-red-600'}>
                          ✓ 8+ characters
                        </span>
                        <span className={passwordStrength.checks.uppercase ? 'text-green-600' : 'text-red-600'}>
                          ✓ Uppercase letter
                        </span>
                        <span className={passwordStrength.checks.lowercase ? 'text-green-600' : 'text-red-600'}>
                          ✓ Lowercase letter
                        </span>
                        <span className={passwordStrength.checks.number ? 'text-green-600' : 'text-red-600'}>
                          ✓ Number
                        </span>
                        <span className={passwordStrength.checks.special ? 'text-green-600' : 'text-red-600'}>
                          ✓ Special character
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Remember Me (Login only) */}
            {isLogin && (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="remember_me"
                  checked={formData.remember_me}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={loading}
                />
                <label className="ml-2 text-sm text-gray-700">
                  Remember me for 7 days
                </label>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>

            {/* Demo Login Button (Login only) */}
            {isLogin && (
              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={loading}
                className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    Setting up demo...
                  </div>
                ) : (
                  'Try Demo Mode'
                )}
              </button>
            )}
          </form>

          {/* Toggle Form */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setErrors({});
                  setSuccess('');
                  setPasswordStrength(null);
                }}
                className="ml-2 text-blue-600 hover:text-blue-700 font-medium"
                disabled={loading}
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Enterprise AI System v2.0</p>
          <p>Secure • Scalable • Intelligent</p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;

