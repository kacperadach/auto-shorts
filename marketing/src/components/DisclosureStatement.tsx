export default function DisclosureStatement() {
  return (
    <div className="flex justify-center w-full my-8">
      <div className="prose font-regular text-base w-1/2">
        <h1 className="text-5xl"> Disclosure Statement</h1>
        <p>
          AutoRepurpose adheres to the{" "}
          <a href="https://developers.google.com/terms/api-services-user-data-policy">
            Google API Services User Data Policy
          </a>
          , including the Limited Use requirements. Our use and transfer to any
          other app of information received from Google APIs will strictly
          follow these policies to ensure user data protection and privacy.
        </p>
      </div>
    </div>
  );
}
