import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  Typography,
  CircularProgress,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const initialSteps = [
  {
    label: 'Search Agent: Searching on internet',
    description: `Searching Google and other online sources for visual and textual content.`,
    loading: false,
    completed: false,
  },
  {
    label: 'Met RAG Agent: Retrieving MET data',
    description: `Querying The Met's archive to retrieve historical fashion images.`,
    loading: false,
    completed: false,
  },
  {
    label: 'Style Agent: Creating style-fashion prompt',
    description: `Analyzing and generating a fashion-specific prompt.`,
    loading: false,
    completed: false,
  },
  {
    label: 'Creative Agent: Generate Image',
    description: `Generating a high-quality fashion image from the prompt.`,
    loading: false,
    completed: false,
  },
  {
    label: 'Creative Agent: Generate Video',
    description: `Creating a cinematic video based on the generated fashion image.`,
    loading: false,
    completed: false,
  },
];

export default function AppStepper({ startTrigger, onFinish }) {
  const [steps, setSteps] = useState(initialSteps);
  const [activeStep, setActiveStep] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    if (startTrigger !== null) {
      const resetSteps = initialSteps.map((step, i) => ({
        ...step,
        loading: i === 0,
        completed: false,
      }));
      setSteps(resetSteps);
      setActiveStep(0);
      setHasStarted(true);
    }
  }, [startTrigger]);

  useEffect(() => {
    if (!hasStarted || activeStep >= steps.length) return;

    const current = steps[activeStep];
    if (current.loading && !current.completed) {
      const timer = setTimeout(() => {
        const nextSteps = steps.map((step, i) => {
          if (i === activeStep) return { ...step, loading: false, completed: true };
          if (i === activeStep + 1) return { ...step, loading: true };
          return step;
        });

        setSteps(nextSteps);
        const nextStep = activeStep + 1;
        setActiveStep(nextStep);

        if (nextStep >= steps.length && onFinish) {
          onFinish(); // ✅ notify parent when finished
        }
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [steps, activeStep, hasStarted, onFinish]);

  const handleBack = () => setActiveStep(prev => Math.max(prev - 1, 0));
  const handleStepClick = (index) => {
    if (index <= activeStep) setActiveStep(index);
  };

  return (
    <Box sx={{ maxWidth: 500, mt: 5 }}>
      <Stepper activeStep={activeStep} orientation="vertical" nonLinear>
        {steps.map((step, index) => (
          <Step key={step.label} completed={step.completed} onClick={() => handleStepClick(index)}>
            <StepLabel
              icon={
                step.completed ? (
                  <CheckCircleIcon fontSize="small" color="success" />
                ) : step.loading ? (
                  <CircularProgress size={16} />
                ) : undefined
              }
            >
              {step.label}
            </StepLabel>
            <StepContent>
              <Typography>{step.description}</Typography>
              <Box sx={{ mb: 2 }}>
                <Button disabled={index === 0} onClick={handleBack} sx={{ mt: 1, mr: 1 }}>
                  Back
                </Button>
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {hasStarted && activeStep >= steps.length && (
      <Typography>All steps completed - you're finished</Typography>
      )}
    </Box>
  );
}
