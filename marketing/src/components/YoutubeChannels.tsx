interface ChannelProps {
  imageUrl: string;
}

function Channel(props: ChannelProps) {
  const { imageUrl } = props;
  return (
    <div className="flex flex-col justify-end items-center mx-4 w-fit flex-shrink-0 hover:bg-primary hover:text-base-100 cursor-pointer transition duration-300 ease-in-out transform hover:scale-105 p-4 rounded-lg shadow-lg">
      <img
        src={imageUrl}
        alt="youtube channel thumbnail"
        className="w-24 h-24 rounded-full object-cover"
      />
    </div>
  );
}

export default function YoutubeChannels() {
  return (
    <>
      <h3 className="font-bold text-4xl text-center">
        Select your YouTube channels to repurpose
      </h3>
      <div className="my-16 flex">
        <Channel imageUrl="/youtube-channels/rogan.webp" />
        <Channel imageUrl="/youtube-channels/mrbeast.webp" />
        <Channel imageUrl="/youtube-channels/lex.webp" />
        <Channel imageUrl="/youtube-channels/dudeperfect.webp" />
        <Channel imageUrl="/youtube-channels/firstwefeast.webp" />
      </div>
      <h3 className="font-bold text-2xl text-center">
        New Uploads get repurposed automatically by our AI
      </h3>
    </>
  );
}
