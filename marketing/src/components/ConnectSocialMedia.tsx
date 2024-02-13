import { FaYoutube, FaInstagram } from "react-icons/fa";

export default function ConnectSocialMedia() {
  return (
    <>
      <h3 className="font-bold text-4xl text-center">
        Connect your Social Media accounts
      </h3>
      <div className="my-16 flex justify-center">
        <FaYoutube size="5rem" color="#FF0000" className="mx-6" />
        <img style={{ width: "5rem", height: "5rem"}} src="/social-media/instagram.webp" />
      </div>
      <h3 className="font-bold text-2xl text-center">
        Repurposed videos will be automatically uploaded to your social media
      </h3>
    </>
  );
}
