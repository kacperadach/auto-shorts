interface HeaderProps {
  blogHref: string;
  loginHref: string;
}

export default function Header(props: HeaderProps) {
  const { blogHref, loginHref } = props;
  return (
    <div className="navbar flex justify-between">
      <div>
        <a href="/" className="flex items-center">
          <img
            src="/logo.svg"
            alt="Auto Repurpose Logo"
            style={{ width: "3rem" }}
          />
          <span className="logoText text-xl ml-2 font-bold">AutoRepurpose</span>
        </a>
      </div>
      <div>
        <a
          className="link no-underline leading-6 border-b-2 border-gray-300 font-bold text-lg mx-2 hover:border-primary hover:text-primary"
          href="/pricing"
        >
          Pricing
        </a>
        <a
          className="link no-underline leading-6 border-b-2 border-gray-300 font-bold text-lg mx-2 hover:border-primary hover:text-primary"
          href={blogHref}
        >
          Blog
        </a>
        <button className="btn btn-primary font-bold text-lg text-white hover:text-primary hover:bg-white mx-2">
          <a href={loginHref}>Log In</a>
        </button>
      </div>
    </div>
  );
}
