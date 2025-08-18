// Wizard state
let currentStep = 1;
let selectedPattern = null;
let configuration = {};

// Get DOM elements
const wizardModal = document.getElementById('wizardModal');
const wizardSteps = document.querySelectorAll('.wizard-step');
const prevButton = document.getElementById('wizard-prev');
const nextButton = document.getElementById('wizard-next');
const configForm = document.getElementById('recursion-config');
const previewCode = document.getElementById('preview-code');

// Pattern templates
const templates = {
    tree: {
        name: 'Tree Recursion',
        config: {
            maxDepth: {
                type: 'number',
                label: 'Maximum Depth',
                default: 3,
                min: 1,
                max: 10
            },
            branchFactor: {
                type: 'number',
                label: 'Branch Factor',
                default: 2,
                min: 1,
                max: 5
            }
        },
        generate: (config) => `def tree_recursion(depth, value):
    if depth >= ${config.maxDepth}:
        return [value]
    
    result = [value]
    for i in range(${config.branchFactor}):
        child_value = value * 10 + (i + 1)
        result.extend(tree_recursion(depth + 1, child_value))
    return result

# Example usage
result = tree_recursion(0, 1)
print("Tree structure:", result)`
    },
    fibonacci: {
        name: 'Fibonacci Series',
        config: {
            cacheEnabled: {
                type: 'checkbox',
                label: 'Enable Memoization',
                default: true
            },
            terms: {
                type: 'number',
                label: 'Number of Terms',
                default: 10,
                min: 1,
                max: 100
            }
        },
        generate: (config) => {
            const useMemo = config.cacheEnabled;
            return `${useMemo ? 'from functools import lru_cache\n\n' : ''}${useMemo ? '@lru_cache(maxsize=None)\n' : ''}def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first ${config.terms} terms
result = [fibonacci(i) for i in range(${config.terms})]
print("Fibonacci sequence:", result)`
        }
    },
    backtrack: {
        name: 'Backtracking',
        config: {
            problemType: {
                type: 'select',
                label: 'Problem Type',
                options: ['subsets', 'permutations'],
                default: 'subsets'
            },
            arraySize: {
                type: 'number',
                label: 'Input Array Size',
                default: 3,
                min: 1,
                max: 5
            }
        },
        generate: (config) => {
            if (config.problemType === 'subsets') {
                return `def generate_subsets(nums):
    def backtrack(start, current):
        result.append(current[:])
        
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    result = []
    backtrack(0, [])
    return result

# Example usage
nums = list(range(1, ${config.arraySize + 1}))  # [1, 2, ..., n]
result = generate_subsets(nums)
print(f"All subsets of {nums}:", result)`
            } else {
                return `def generate_permutations(nums):
    def backtrack(current):
        if len(current) == len(nums):
            result.append(current[:])
            return
            
        for num in nums:
            if num not in current:
                current.append(num)
                backtrack(current)
                current.pop()
    
    result = []
    backtrack([])
    return result

# Example usage
nums = list(range(1, ${config.arraySize + 1}))  # [1, 2, ..., n]
result = generate_permutations(nums)
print(f"All permutations of {nums}:", result)`
            }
        }
    }
};

// Event listeners for pattern selection
document.querySelectorAll('[data-pattern]').forEach(button => {
    button.addEventListener('click', () => {
        selectedPattern = button.dataset.pattern;
        document.querySelectorAll('[data-pattern]').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
    });
});

// Create configuration form for a pattern
function createConfigForm(pattern) {
    const template = templates[pattern];
    configForm.innerHTML = '';
    
    Object.entries(template.config).forEach(([key, field]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = field.label;
        formGroup.appendChild(label);
        
        let input;
        if (field.type === 'select') {
            input = document.createElement('select');
            input.className = 'form-select';
            field.options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option;
                opt.textContent = option.charAt(0).toUpperCase() + option.slice(1);
                input.appendChild(opt);
            });
        } else if (field.type === 'checkbox') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.className = 'form-check-input';
            label.className = 'form-check-label';
            formGroup.className = 'mb-3 form-check';
        } else {
            input = document.createElement('input');
            input.type = field.type;
            input.className = 'form-control';
            if (field.min !== undefined) input.min = field.min;
            if (field.max !== undefined) input.max = field.max;
        }
        
        input.id = key;
        input.value = field.default;
        if (field.type === 'checkbox') {
            input.checked = field.default;
        }
        
        formGroup.appendChild(input);
        configForm.appendChild(formGroup);
    });
}

// Navigate between wizard steps
function showStep(step) {
    wizardSteps.forEach(s => {
        s.classList.add('d-none');
        if (parseInt(s.dataset.step) === step) {
            s.classList.remove('d-none');
        }
    });
    
    currentStep = step;
    prevButton.disabled = currentStep === 1;
    
    if (currentStep === 3) {
        nextButton.textContent = 'Generate';
    } else {
        nextButton.textContent = 'Next';
    }
}

// Handle wizard navigation
prevButton.addEventListener('click', () => {
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
});

nextButton.addEventListener('click', () => {
    if (currentStep === 1 && !selectedPattern) {
        alert('Please select a recursion pattern');
        return;
    }
    
    if (currentStep === 1) {
        createConfigForm(selectedPattern);
    } else if (currentStep === 2) {
        // Gather configuration
        configuration = {};
        const template = templates[selectedPattern];
        Object.keys(template.config).forEach(key => {
            const input = document.getElementById(key);
            configuration[key] = input.type === 'checkbox' ? input.checked : input.value;
        });
        
        // Generate and show preview
        const generatedCode = templates[selectedPattern].generate(configuration);
        previewCode.value = generatedCode;
    } else if (currentStep === 3) {
        // Insert code into main editor
        editor.setValue(previewCode.value);
        const modal = bootstrap.Modal.getInstance(wizardModal);
        modal.hide();
        showStep(1);
        return;
    }
    
    showStep(currentStep + 1);
});

// Reset wizard when modal is closed
wizardModal.addEventListener('hidden.bs.modal', () => {
    showStep(1);
    selectedPattern = null;
    configuration = {};
    document.querySelectorAll('[data-pattern]').forEach(btn => {
        btn.classList.remove('active');
    });
});
