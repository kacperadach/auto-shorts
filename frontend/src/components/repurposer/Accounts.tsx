import { useEffect, useState } from "react";
import { Repurposer } from "../../lib/types";
import {
  addErrorAlert,
  addSuccessAlert,
  getSocialMediaAccounts,
  repurposers,
  socialMediaAccounts,
} from "../../lib/signals";
import { FaYoutube } from "react-icons/fa6";
import { FaPlus } from "react-icons/fa";
import {
  addSocialMediaAccountToRepurposer,
  deleteSocialMediaAccount,
  initiate_oauth_youtube,
  removeSocialMediaAccountFromRepurposer,
} from "../../lib/api";
import {
  BsArrowLeft,
  BsArrowRight,
  BsBack,
  BsPencil,
  BsPlusCircle,
  BsTrash,
} from "react-icons/bs";
import Swal from "sweetalert2";

interface AccountsProps {
  selectedRepurposer: Repurposer;
}

export default function Accounts(props: AccountsProps) {
  const { selectedRepurposer } = props;

  const [showAllAccounts, setShowAllAccounts] = useState(false);
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [consentChecked, setConsentChecked] = useState(false);

  const youtubeAccount = selectedRepurposer.social_media_accounts.find(
    (account) => {
      return account.platform === "youtube";
    }
  );

  useEffect(() => {
    if (!modalOpen) {
      setConsentChecked(false);
    }
  }, [modalOpen]);

  useEffect(() => {
    getSocialMediaAccounts();
  }, []);

  return (
    <>
      {!showAllAccounts && (
        <div>
          <h1>Social Accounts</h1>
          <button
            className="btn btn-primary text-base-100"
            onClick={async () => {
              setShowAllAccounts(true);
            }}
          >
            All Connected Accounts <BsArrowRight size="1.5rem" />
          </button>
          <div className="m-2 ">
            <div className="card w-1/3 bg-base-100 shadow-xl p-2">
              <div className="flex items-center m-2">
                <FaYoutube color="#FF0000" size="2rem" className="mr-2" />
                <h1 className="m-0">YouTube Account</h1>
              </div>
              {!youtubeAccount && (
                <div className="flex flex-col justify-center items-center border-2 border-secondary border-dashed p-8 m-8 h-full">
                  <h2>No Account Connected</h2>
                  <button
                    className="btn btn-circle btn-outline"
                    onClick={() => {
                      setIsAddingAccount(true);
                      setShowAllAccounts(true);
                    }}
                  >
                    <FaPlus />
                  </button>
                </div>
              )}
              {youtubeAccount && (
                <div className="flex flex-col items-center">
                  <h3 className="text-sm text-ellipsis overflow-hidden text-center">
                    {youtubeAccount.title}
                  </h3>
                  <img
                    src={youtubeAccount.thumbnail_url}
                    alt="youtube channel thumbnail"
                    className="w-24 h-24 rounded-full object-cover"
                  />
                  <div className="flex">
                    <div className="tooltip" data-tip="Remove Account">
                      <button
                        className="btn btn-circle btn-outline mr-2"
                        onClick={() => {
                          Swal.fire({
                            title: "Warning!",
                            text: "Are you sure you want to remove this account?",
                            icon: "warning",
                            confirmButtonText: "Yes",
                            showCancelButton: true,
                            cancelButtonText: "No",
                            customClass: "text-primary",
                            confirmButtonColor: "black",
                          }).then(async (result) => {
                            if (result.isConfirmed) {
                              const response =
                                await removeSocialMediaAccountFromRepurposer(
                                  youtubeAccount.id,
                                  selectedRepurposer.id
                                );
                              if (!response.success) {
                                addErrorAlert(
                                  "Failed to remove account from repurposer"
                                );
                                return;
                              }
                              addSuccessAlert(
                                "Account removed from repurposer"
                              );
                              repurposers.value = [
                                ...repurposers.value.map((r) => {
                                  if (r.id !== selectedRepurposer.id) {
                                    return r;
                                  }
                                  return {
                                    ...r,
                                    social_media_accounts:
                                      r.social_media_accounts.filter(
                                        (c) => c.id !== youtubeAccount.id
                                      ),
                                  };
                                }),
                              ];
                            }
                          });
                        }}
                      >
                        <BsTrash size="1.5rem" />
                      </button>
                    </div>
                    <div className="tooltip" data-tip="Change Account">
                      <button
                        className="btn btn-circle btn-outline"
                        onClick={() => {
                          setIsAddingAccount(true);
                          setShowAllAccounts(true);
                        }}
                      >
                        <BsPencil size="1.5rem" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <dialog
        id="my_modal_1"
        className="modal bg-black bg-opacity-50"
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      >
        <div className="modal-box">
          <h3 className="font-bold text-lg">Consent to Data Use</h3>
          <p>
            We use AI models to process transcriptions of your YouTube videos
            and utilize basic channel information (such as titles and
            thumbnails) for in-app display purposes. This involves sharing
            transcribed text from YouTube videos (not personal data) with
            trusted AI providers like OpenAI. Your consent is required for this
            process, separate from Google login consent. You can opt out at any
            time. For more details, see our{" "}
            <a href="https://www.autorepurpose.com/privacy-policy">
              Privacy Policy.
            </a>
          </p>
          <div className="form-control">
            <label className="label cursor-pointer w-fit">
              <input
                type="checkbox"
                className="checkbox mr-2"
                checked={consentChecked}
                onChange={(e) => setConsentChecked(e.target.checked)}
              />
              <span className="label-text">
                I agree to the use of my data as described above.
              </span>
            </label>
          </div>
          <div className="flex w-full justify-between">
            <div className="modal-action">
              <form method="dialog">
                <button
                  className={`btn ${
                    consentChecked ? "btn-primary" : "btn-disabled"
                  }`}
                  onClick={async () => {
                    const response = await initiate_oauth_youtube();
                    if (!response.success) {
                      addErrorAlert("Failed to initiate account connection");
                      return;
                    }

                    const { auth_url } = response.data;

                    window.open(auth_url, "_blank");
                  }}
                >
                  Continue
                </button>
              </form>
            </div>
            <div className="modal-action">
              <form method="dialog">
                <button className="btn">Close</button>
              </form>
            </div>
          </div>
        </div>
      </dialog>
      {showAllAccounts && (
        <div>
          <div className="flex items-center mb-6">
            <button
              className="btn mr-2"
              onClick={() => {
                setShowAllAccounts(false);
                setIsAddingAccount(false);
              }}
            >
              <BsArrowLeft size="1.5rem" />
            </button>
            <h1 className="m-0">All Accounts</h1>
          </div>
          <button
            className="btn btn-primary text-base-100"
            onClick={async () => {
              setModalOpen(true);
            }}
          >
            Add New Account <BsPlusCircle size="1.5rem" />
          </button>
          <div className="grid grid-cols-6 gap-8 m-2">
            {socialMediaAccounts.value.map((account) => {
              return (
                <div
                  key={account.id}
                  className="flex flex-col justify-end items-center mx-4 w-auto flex-shrink-0 hover:bg-accent cursor-pointer transition duration-300 ease-in-out transform hover:scale-105 p-4 rounded-lg shadow-lg"
                  onClick={async () => {
                    if (!isAddingAccount) {
                      return;
                    }
                    const response = await addSocialMediaAccountToRepurposer(
                      account.id,
                      selectedRepurposer.id
                    );
                    if (!response.success) {
                      addErrorAlert("Failed to add account to repurposer");
                      return;
                    }
                    addSuccessAlert("Account added to repurposer");
                    setIsAddingAccount(false);
                    setShowAllAccounts(false);
                    repurposers.value = [
                      ...repurposers.value.map((r) => {
                        if (r.id !== selectedRepurposer.id) {
                          return r;
                        }
                        return {
                          ...r,
                          social_media_accounts: [
                            ...r.social_media_accounts,
                            account,
                          ],
                        };
                      }),
                    ];
                  }}
                >
                  <h3 className="text-sm text-ellipsis overflow-hidden text-center">
                    {account.title}
                  </h3>
                  <img
                    src={account.thumbnail_url}
                    alt="youtube channel thumbnail"
                    className="w-24 h-24 rounded-full object-cover"
                  />
                  <button
                    className="btn btn-circle btn-outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      Swal.fire({
                        title: "Warning!",
                        text: "Are you sure you want to delete this account? All personal data related to this account will be deleted.",
                        icon: "warning",
                        confirmButtonText: "Yes",
                        showCancelButton: true,
                        cancelButtonText: "No",
                        customClass: "text-primary",
                        confirmButtonColor: "black",
                      }).then(async (result) => {
                        if (result.isConfirmed) {
                          const response = await deleteSocialMediaAccount(
                            account.id
                          );
                          if (response.success) {
                            addSuccessAlert("Account deleted successfully");
                            socialMediaAccounts.value =
                              socialMediaAccounts.value.filter(
                                (a) => a.id !== account.id
                              );
                          } else {
                            addErrorAlert("Failed to delete account");
                          }
                        }
                      });
                    }}
                  >
                    <BsTrash />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
