#!/usr/bin/env python3
"""
Advanced Security Analysis for Claude-Jester Desktop Extension
Comprehensive code security scanning and vulnerability detection
"""

import re
import hashlib
import ast
import logging
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SecurityViolation:
    """Represents a security violation found in code"""
    severity: str  # low, medium, high, critical
    category: str  # injection, file_access, network, system, etc.
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    pattern: Optional[str] = None

class SecurityPattern:
    """Represents a security pattern to check"""
    def __init__(self, pattern: str, severity: str, category: str, 
                 description: str, suggestion: str = ""):
        self.pattern = pattern
        self.severity = severity
        self.category = category
        self.description = description
        self.suggestion = suggestion

class AdvancedSecurityAnalyzer:
    """Advanced security analyzer with multiple detection methods"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.ast_checkers = self._initialize_ast_checkers()
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_patterns(self) -> List[SecurityPattern]:
        """Initialize security patterns for detection"""
        return [
            # Critical patterns
            SecurityPattern(
                r"os\.system\s*\(",
                "critical", "system",
                "Direct system command execution",
                "Use subprocess with specific arguments instead"
            ),
            SecurityPattern(
                r"eval\s*\(",
                "critical", "injection",
                "Dynamic code evaluation - code injection risk",
                "Avoid eval() - use specific parsing functions"
            ),
            SecurityPattern(
                r"exec\s*\(",
                "critical", "injection", 
                "Dynamic code execution - code injection risk",
                "Avoid exec() - use specific parsing functions"
            ),
            SecurityPattern(
                r"subprocess\.(call|run|Popen)\s*\(\s*shell\s*=\s*True",
                "high", "system",
                "Shell command execution with shell=True",
                "Use shell=False and pass arguments as list"
            ),
            
            # High severity patterns
            SecurityPattern(
                r"__import__\s*\(",
                "high", "injection",
                "Dynamic module import",
                "Use static imports when possible"
            ),
            SecurityPattern(
                r"compile\s*\(",
                "high", "injection",
                "Dynamic code compilation", 
                "Avoid dynamic compilation"
            ),
            SecurityPattern(
                r"open\s*\(\s*['\"].*\.\./",
                "high", "file_access",
                "Path traversal attempt in file access",
                "Validate and sanitize file paths"
            ),
            
            # Medium severity patterns  
            SecurityPattern(
                r"import\s+os\b",
                "medium", "system",
                "Operating system access imported",
                "Review OS access requirements"
            ),
            SecurityPattern(
                r"import\s+subprocess\b",
                "medium", "system", 
                "Subprocess module imported",
                "Review subprocess usage for security"
            ),
            SecurityPattern(
                r"import\s+(urllib|requests|httplib)\b",
                "medium", "network",
                "Network access module imported",
                "Review network access requirements"
            ),
            SecurityPattern(
                r"import\s+socket\b",
                "medium", "network",
                "Socket programming imported",
                "Review socket usage for security"
            ),
            
            # Low severity patterns
            SecurityPattern(
                r"import\s+pickle\b",
                "low", "serialization",
                "Pickle module can execute arbitrary code",
                "Consider safer serialization formats like JSON"
            ),
            SecurityPattern(
                r"input\s*\(",
                "low", "input",
                "User input without validation",
                "Validate and sanitize user input"
            )
        ]
    
    def _initialize_ast_checkers(self) -> List[callable]:
        """Initialize AST-based security checkers"""
        return [
            self._check_dangerous_functions,
            self._check_import_statements,
            self._check_string_operations,
            self._check_file_operations
        ]
    
    def _initialize_compliance_rules(self) -> Dict[str, List[str]]:
        """Initialize compliance rules for different standards"""
        return {
            "OWASP": [
                "injection", "broken_auth", "sensitive_data", 
                "xxe", "broken_access", "security_misconfig",
                "xss", "insecure_deser", "vulnerable_components", "logging"
            ],
            "SOC2": [
                "access_control", "encryption", "monitoring", 
                "backup", "incident_response"
            ],
            "ISO27001": [
                "risk_assessment", "access_management", "cryptography",
                "physical_security", "operational_security"
            ]
        }
    
    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Comprehensive security analysis of code"""
        violations = []
        
        try:
            # Pattern-based analysis
            pattern_violations = self._analyze_patterns(code)
            violations.extend(pattern_violations)
            
            # AST-based analysis (for Python)
            if language.lower() == "python":
                try:
                    tree = ast.parse(code)
                    ast_violations = self._analyze_ast(tree, code)
                    violations.extend(ast_violations)
                except SyntaxError as e:
                    violations.append(SecurityViolation(
                        "medium", "syntax",
                        f"Syntax error may indicate obfuscated code: {e}",
                        line_number=getattr(e, 'lineno', None)
                    ))
            
            # Complexity analysis
            complexity_score = self._analyze_complexity(code)
            if complexity_score > 50:
                violations.append(SecurityViolation(
                    "low", "complexity",
                    f"High code complexity ({complexity_score}) may hide security issues",
                    suggestion="Break down complex functions for easier review"
                ))
            
            # Generate overall assessment
            risk_level = self._calculate_risk_level(violations)
            compliance_status = self._check_compliance_violations(violations)
            
            return {
                "risk_level": risk_level,
                "violations": [self._violation_to_dict(v) for v in violations],
                "compliance_status": compliance_status,
                "complexity_score": complexity_score,
                "total_violations": len(violations),
                "critical_violations": len([v for v in violations if v.severity == "critical"]),
                "recommendations": self._generate_recommendations(violations)
            }
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {
                "risk_level": "unknown",
                "violations": [],
                "error": str(e),
                "compliance_status": {},
                "complexity_score": 0,
                "total_violations": 0,
                "critical_violations": 0,
                "recommendations": []
            }
    
    def _analyze_patterns(self, code: str) -> List[SecurityViolation]:
        """Analyze code using regex patterns"""
        violations = []
        
        for pattern_obj in self.patterns:
            matches = re.finditer(pattern_obj.pattern, code, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Find line number
                line_number = code[:match.start()].count('\n') + 1
                
                violation = SecurityViolation(
                    severity=pattern_obj.severity,
                    category=pattern_obj.category,
                    description=pattern_obj.description,
                    line_number=line_number,
                    suggestion=pattern_obj.suggestion,
                    pattern=pattern_obj.pattern
                )
                violations.append(violation)
        
        return violations
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Analyze code using AST parsing"""
        violations = []
        
        for checker in self.ast_checkers:
            try:
                checker_violations = checker(tree, code)
                violations.extend(checker_violations)
            except Exception as e:
                logger.warning(f"AST checker failed: {e}")
        
        return violations
    
    def _check_dangerous_functions(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous function calls"""
        violations = []
        dangerous_functions = {
            'eval': 'critical',
            'exec': 'critical', 
            'compile': 'high',
            '__import__': 'high',
            'getattr': 'medium',
            'setattr': 'medium',
            'delattr': 'medium'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in dangerous_functions:
                        violations.append(SecurityViolation(
                            severity=dangerous_functions[func_name],
                            category="dangerous_function",
                            description=f"Use of dangerous function: {func_name}",
                            line_number=node.lineno,
                            suggestion=f"Avoid using {func_name} function"
                        ))
        
        return violations
    
    def _check_import_statements(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for suspicious imports"""
        violations = []
        suspicious_modules = {
            'os': 'medium',
            'subprocess': 'medium', 
            'socket': 'medium',
            'urllib': 'medium',
            'requests': 'medium',
            'pickle': 'low',
            'marshal': 'low',
            'ctypes': 'high'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in suspicious_modules:
                        violations.append(SecurityViolation(
                            severity=suspicious_modules[module_name],
                            category="suspicious_import",
                            description=f"Import of potentially dangerous module: {module_name}",
                            line_number=node.lineno,
                            suggestion=f"Review usage of {module_name} module"
                        ))
        
        return violations
    
    def _check_string_operations(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous string operations"""
        violations = []
        
        for node in ast.walk(tree):
            # Check for string formatting that might lead to injection
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'format'):
                    violations.append(SecurityViolation(
                        severity="low",
                        category="string_injection",
                        description="String formatting may be vulnerable to injection",
                        line_number=node.lineno,
                        suggestion="Validate and sanitize format arguments"
                    ))
        
        return violations
    
    def _check_file_operations(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for unsafe file operations"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check for path traversal patterns in file operations
                    if node.args:
                        if isinstance(node.args[0], ast.Constant):
                            path = str(node.args[0].value)
                            if '..' in path or path.startswith('/'):
                                violations.append(SecurityViolation(
                                    severity="high",
                                    category="path_traversal",
                                    description="Potential path traversal in file operation",
                                    line_number=node.lineno,
                                    suggestion="Validate and sanitize file paths"
                                ))
        
        return violations
    
    def _analyze_complexity(self, code: str) -> int:
        """Calculate code complexity score"""
        complexity = 1  # Base complexity
        
        # Count control structures
        control_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with']
        for keyword in control_keywords:
            complexity += code.count(keyword)
        
        # Count function definitions
        complexity += code.count('def ')
        complexity += code.count('class ')
        
        return complexity
    
    def _calculate_risk_level(self, violations: List[SecurityViolation]) -> str:
        """Calculate overall risk level"""
        if not violations:
            return "low"
        
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2, 
            "low": 1
        }
        
        total_score = sum(severity_weights.get(v.severity, 0) for v in violations)
        
        if total_score >= 20:
            return "critical"
        elif total_score >= 10:
            return "high"
        elif total_score >= 5:
            return "medium"
        else:
            return "low"
    
    def _check_compliance_violations(self, violations: List[SecurityViolation]) -> Dict[str, Any]:
        """Check for compliance violations"""
        compliance_status = {}
        
        for standard, categories in self.compliance_rules.items():
            violations_in_standard = []
            for violation in violations:
                if violation.category in categories or any(cat in violation.description.lower() for cat in categories):
                    violations_in_standard.append(violation)
            
            compliance_status[standard] = {
                "violations": len(violations_in_standard),
                "status": "fail" if violations_in_standard else "pass",
                "risk_areas": list(set(v.category for v in violations_in_standard))
            }
        
        return compliance_status
    
    def _generate_recommendations(self, violations: List[SecurityViolation]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Category-based recommendations
        categories = set(v.category for v in violations)
        
        if "injection" in categories:
            recommendations.append("Implement input validation and sanitization")
            recommendations.append("Use parameterized queries and prepared statements")
        
        if "system" in categories:
            recommendations.append("Minimize system-level access")
            recommendations.append("Use containerization for additional isolation")
        
        if "network" in categories:
            recommendations.append("Validate all network requests and responses")
            recommendations.append("Use HTTPS for all network communications")
        
        if "file_access" in categories:
            recommendations.append("Implement proper file access controls")
            recommendations.append("Validate and sanitize all file paths")
        
        return recommendations
    
    def _violation_to_dict(self, violation: SecurityViolation) -> Dict[str, Any]:
        """Convert violation to dictionary"""
        return {
            "severity": violation.severity,
            "category": violation.category,
            "description": violation.description,
            "line_number": violation.line_number,
            "suggestion": violation.suggestion,
            "pattern": violation.pattern
        }
