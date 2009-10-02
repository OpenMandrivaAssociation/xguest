Summary: Creates xguest user as a locked down user 
Name: xguest
Version: 1.0.7
Release: %mkrel 1
License: GPLv2+
Group:   System/Base
BuildArch: noarch
Source:  http://people.fedoraproject.org/~dwalsh/xguest/%{name}-%{version}.tar.bz2
patch:   xguest-namespace.patch
URL:     http://people.fedoraproject.org/~dwalsh/xguest/

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires(pre): pam >= 0.99.8.1
# fedora has splited sabayon-apply to have smaller requires:
Requires(post): sabayon sabayon-admin
Requires: gdm >= 2.20.10-6mdv

# TODO:
# - check if /usr/sbin/gdm-safe-restart is needed in /etc/X11.gdm/PostSession/Default
# - prevent logging on console

%description
Installing this package sets up the xguest user to be used as a temporary
account to switch to or as a kiosk user account.
The user is only allowed to log in via gdm.  The home and temporary directories
of the user will be polyinstantiated and mounted on tmpfs.

WARNING: unlike Fedora, where the account is disabled unless SELinux is in
enforcing mode and where it's only accessible through gdm/kdm/xdm, it's
accessible from the console too.

%prep
%setup -q
%patch -p1 -b .namespace

%build

%clean
%{__rm} -fR %{buildroot}

%install
%{__rm} -fR %{buildroot}
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/desktop-profiles
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/security/namespace.d/ls
install -m0644 xguest.zip %{buildroot}/%{_sysconfdir}/desktop-profiles/
install -m0644 xguest.conf %{buildroot}/%{_sysconfdir}/security/namespace.d/

%pre
if [ $1 -eq 1 ]; then
	useradd -p '' -c "Guest" xguest || :
fi

%post
if [ $1 -eq 1 ]; then

# Add two directories to /etc/skell so pam_namespace will label properly
mkdir /etc/skel/.mozilla 2> /dev/null
mkdir /etc/skel/.gnome2 2> /dev/null

/usr/bin/python << __eof
from sabayon import userdb
db = userdb.get_database()
db.set_profile("xguest", "xguest.zip")
__eof

# prevent remote login:
echo xguest >> /etc/ssh/denyusers 

fi

%files
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/desktop-profiles/xguest.zip
%{_sysconfdir}/security/namespace.d/
%doc README LICENSE

%preun
if [ $1 -eq 0 ]; then

/usr/bin/python << __eof
from sabayon import userdb
db = userdb.get_database()
db.set_profile("xguest", "")
__eof

userdel -r xguest

# remove forbiden SSH:
sed -i '/^xguest/d' /etc/ssh/denyusers

fi

