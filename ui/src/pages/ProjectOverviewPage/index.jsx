import * as React from 'react';
import {Container, Typography, Box, Paper} from '@mui/material';

export default function ProjectOverviewPage() {
  return (
       <div style={{
          width: '100%',
          minHeight: '100vh',  // ✅ Ensures full screen height
          overflow: 'auto',
          background: 'linear-gradient(-45deg, #1e3c72, #2a5298, #2980b9, #6dd5fa)',
          backgroundSize: '400% 400%',  // ✅ Required for animated flow effect
          animation: 'gradientFlow 18s ease infinite',
        }}>
              <style>{`
        @keyframes gradientFlow {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>
    <Container >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            my: 10,
            borderRadius: 4,
            width: '100%',
          }}
        >
        <Typography variant="h3" gutterBottom>
          Project Overview
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          This project is an AI-driven fashion design assistant that transforms user prompts into rich visual outputs using a modular, multi-agent system. Built specifically for fashion concept generation, it automates every step — from idea interpretation to high-fidelity visual creation — by orchestrating a team of intelligent agents.
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          At its core, the platform uses a multi-agent architecture, where each agent specializes in a discrete task: analyzing user input, retrieving visual references, generating descriptive fashion language, producing images, and organizing media into moodboards. These agents communicate asynchronously to create a dynamic, composable workflow tailored to creative exploration.
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          Users can input vague or expressive fashion ideas, and the system responds with structured, historically grounded outputs — including AI-generated images, curated archive references, and CSV reports summarizing matches and distances. Everything is generated, enhanced, and visualized in real time.
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          The platform is ideal for fashion designers, educators, archivists, and creators who need rapid visual prototyping, moodboard generation, or access to stylistic inspiration derived from curated datasets and open-access museum archives.
        </Typography>

        <Typography variant="body1" color="text.secondary" paragraph>
          By combining LLMs, retrieval-augmented generation, and autonomous tool orchestration, this project offers a glimpse into the future of creative automation — where intelligent agents assist with storytelling, research, and visual design, all in a single, seamless pipeline.
        </Typography>
      </Paper>
    </Container>
    </div>
  );
}
