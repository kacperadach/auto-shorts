import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";
import { userSession } from "./lib/signals";
import LoadingSpinner from "./components/auth/LoadingSpinner";
import Login from "./components/auth/Login";
import Navbar from "./components/layout/Navbar";
import Home from "./components/home/Home";
import AlertBanner from "./components/layout/AlertBanner";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Repurposer from "./components/repurposer/Repurporser";
import Channel from "./components/channel/Channel";
import RepurposerRun from "./components/run/RepurposerRun";
import Oauth from "./components/oauth/Oauth";
import { VideoPlayer } from "./components/video/VideoPlayer";

function App() {
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      userSession.value = session;
      setAuthChecked(true);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      userSession.value = session;
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!authChecked) {
    return <LoadingSpinner />;
  }

  if (!userSession.value) {
    return <Login />;
  }

  return (
    <div className="App h-full flex flex-col">
      <BrowserRouter>
        <AlertBanner />
        <Navbar />
        <div className="flex-grow overflow-y-auto">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Home />} />
            <Route path="/repurposer/:repurposerId" element={<Repurposer />} />
            <Route
              path="/repurposer/:repurposerId/channel/:channelId"
              element={<Channel />}
            />
            <Route
              path="/repurposer/:repurposerId/run/:runId"
              element={<RepurposerRun />}
            />
            <Route path="player" element={<VideoPlayer />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
