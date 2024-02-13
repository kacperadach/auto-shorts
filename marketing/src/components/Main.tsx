import ConnectSocialMedia from "./ConnectSocialMedia";
import Customize from "./Customize";
import Growth from "./Growth";
import LaurelPraise from "./LaurelPraise";
import Testimonial from "./Testimonial";
import Wave from "./Wave";
import YoutubeChannels from "./YoutubeChannels";

interface MainProps {
  appHref: string;
}

export default function Main(props: MainProps) {
  const { appHref } = props;

  return (
    <main className="w-full">
      <div className="w-full flex justify-center mt-8">
        <div className="flex w-2/3">
          <div className="w-3/5">
            <h1 className="text-6xl font-bold tracking-tight ">
              Fully Automate your Shorts Channel with AI
            </h1>
            <h2 className="text-2xl my-3 font-semibold">
              Save time and money with 100% hands-off content repurposing with
              the help of AI
            </h2>
            <div className="font-semibold text-xl">
              <div className="my-1">
                <a
                  href="#anchor-one"
                  className="text-primary mr-2 underline underline-offset-4 cursor-pointer hover:text-secondary"
                >
                  Select your channels
                </a>
                <span>- new uploads automatically get repurposed</span>
              </div>
              <div className="my-1">
                <a
                  href="#anchor-two"
                  className="text-primary mr-2 underline underline-offset-4 cursor-pointer hover:text-secondary"
                >
                  Customize your shorts
                </a>
                <span>- add subtitles, secondary videos and pick topics</span>
              </div>
              <div className="my-1">
                <a
                  href="#anchor-three"
                  className="text-primary mr-2 underline underline-offset-4 cursor-pointer hover:text-secondary"
                >
                  Connect your social media
                </a>
                <span>- for automatic uploads</span>
              </div>
              <div className="my-1">
                <a
                  href="#anchor-four"
                  className="text-primary mr-2 underline underline-offset-4 cursor-pointer hover:text-secondary"
                >
                  Kick back and relax
                </a>
                <span>- and watch as your channel grows effortlessly</span>
              </div>
              <LaurelPraise />
            </div>
          </div>
          <div className="flex h-full w-2/5 items-center justify-center">
            <button className="btn btn-primary text-2xl px-16 h-16 flex items-center text-white bg-gradient-to-r from-primary to-accent border-none hover:scale-110">
              <a href={appHref}>Get Started</a>
            </button>
          </div>
        </div>
      </div>

      <Wave direction="up" colorClass="oklch(var(--p))" />
      <div className="w-full bg-primary bg-gradient-to-b from-primary to-accent flex justify-center">
        <div className="m-8">
          <Testimonial
            name="Ethan Parker"
            text="AutoRepurpose has saved me so much time and money."
            imageSrc="/testimonial/Ethan_Parker.webp"
            position="left"
          />
        </div>
        <div className="m-8">
          <Testimonial
            name="Olivia Bennett"
            text="Easy and Simple to setup. I have no need for a social media manager anymore."
            imageSrc="/testimonial/Olivia_Bennett.webp"
            position="center"
          />
        </div>
        <div className="m-8">
          <Testimonial
            name="James Marshall"
            text="A fully automated shorts channel is the way to go for aspiring content creators."
            imageSrc="/testimonial/James_Marshall.webp"
            position="right"
          />
        </div>
      </div>
      <Wave direction="down" colorClass="oklch(var(--a))" />

      <div className="flex justify-center py-16">
        <div id="anchor-one">
          <YoutubeChannels />
        </div>
      </div>

      <Wave direction="up" colorClass="oklch(var(--a))" />
      <div className="flex justify-center py-16 bg-gradient-to-b from-accent to-secondary">
        <div
          id="anchor-two"
          className="backdrop-blur-xl bg-white/10 p-8 rounded"
        >
          <Customize />
        </div>
      </div>
      <Wave direction="down" colorClass="oklch(var(--s))" />

      <div className="flex justify-center py-16">
        <div id="anchor-three">
          <ConnectSocialMedia />
        </div>
      </div>

      {/* <Wave direction="up" colorClass="oklch(var(--s))" /> */}
      <div className="flex justify-center py-32 bg-accent text-base-100">
        <div id="anchor-four">
          <Growth />
        </div>
      </div>
    </main>
  );
}
