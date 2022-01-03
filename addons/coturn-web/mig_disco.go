package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"

	metadata "cloud.google.com/go/compute/metadata"
	"github.com/jpillora/backoff"
)

type migDiscoIPsSync struct {
	sync.Mutex
	ExternalIPs   []string
	LastUpdate    time.Time
	FilterPattern *regexp.Regexp
	ProjectID     string
	AccessToken   string
}

func (mips *migDiscoIPsSync) Update() {
	if time.Now().Sub(mips.LastUpdate) < 60*time.Second {
		return
	}

	mips.AccessToken = popVarFromEnv("ACCESS_TOKEN", false, "")
	if len(mips.AccessToken) == 0 {
		var err error
		mips.AccessToken, err = getDefaultSAToken()
		if err != nil {
			log.Fatalf("%v", err)
		}
	}

	b := &backoff.Backoff{
		//These are the defaults
		Min:    100 * time.Millisecond,
		Max:    30 * time.Second,
		Factor: 2,
		Jitter: false,
	}
	for {
		if err := mips.getMigDiscoIPs(); err != nil {
			log.Printf("ERROR: %v", err)
			time.Sleep(b.Duration())
			continue
		}
		b.Reset()
		mips.LastUpdate = time.Now()
		break
	}
}

func (mips *migDiscoIPsSync) getMigDiscoIPs() error {
	// Find all instance groups matching the mig filter pattern.
	groupURIs, err := listInstanceGroups(mips.FilterPattern, mips.ProjectID, mips.AccessToken)
	if err != nil {
		return err
	}

	// Clear out old list of IPs.
	newIPs := make([]string, 0)

	for _, migSelfLink := range groupURIs {
		uris, err := getInstanceGroupInstancesURIs(migSelfLink, mips.ProjectID, mips.AccessToken)
		if err != nil {
			return err
		}

		// Fetch external IPs of the instances.
		if len(uris) > 0 {
			for _, uri := range uris {
				ip, err := getInstanceExternalIP(uri, mips.AccessToken)
				if err != nil {
					return err
				}
				newIPs = append(newIPs, ip)
			}
		} else {
			log.Printf("WARN: no instances found in managed instance group: %s", migSelfLink)
		}
	}

	mips.Lock()
	defer mips.Unlock()
	mips.ExternalIPs = newIPs

	return nil
}

func getDefaultSAToken() (string, error) {
	token := ""

	type saTokenResponse struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int    `json:"expires_in"`
		TokenType   string `json:"token_type"`
	}

	body, err := metadata.Get("instance/service-accounts/default/token")
	if err != nil {
		log.Fatalf("%v", err)
	}

	var tokenResp saTokenResponse
	if err := json.Unmarshal([]byte(body), &tokenResp); err != nil {
		return token, err
	}

	return tokenResp.AccessToken, nil
}

func getInstanceGroupInstancesURIs(migSelfLink, projectID, accessToken string) ([]string, error) {
	uris := []string{}

	type regionInstanceGroupsListInstance struct {
		InstanceURI string `json:"instance"`
	}
	type listInstancesResponse struct {
		Items []regionInstanceGroupsListInstance `json:"items"`
	}

	migListURI := fmt.Sprintf("%s/listInstances", strings.ReplaceAll(migSelfLink, "https://www.googleapis.com/", "https://compute.googleapis.com/"))

	client := &http.Client{}
	req, err := http.NewRequest("POST", migListURI, nil)
	req.Header.Set("User-Agent", "Selkies_Controller/1.0")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))
	resp, err := client.Do(req)
	if err != nil {
		return uris, err
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return uris, err
	}

	var listResp listInstancesResponse
	if err := json.Unmarshal(body, &listResp); err != nil {
		return uris, err
	}

	for _, i := range listResp.Items {
		uris = append(uris, i.InstanceURI)
	}

	return uris, nil
}

func listInstanceGroups(filterPattern *regexp.Regexp, projectID, accessToken string) ([]string, error) {
	groupList := []string{}

	type instanceGroup struct {
		Name     string `json:"name"`
		SelfLink string `json:"selfLink"`
	}
	type locationResults struct {
		InstanceGroups []instanceGroup `json:"instanceGroups"`
	}
	type listInstanceGroupsResponse struct {
		Items map[string]locationResults `json:"items"`
	}

	listURL := fmt.Sprintf("https://compute.googleapis.com/compute/v1/projects/%s/aggregated/instanceGroups?alt=json&includeAllScopes=True&maxResults=500", projectID)

	client := &http.Client{}
	req, err := http.NewRequest("GET", listURL, nil)
	req.Header.Set("User-Agent", "Selkies_Controller/1.0")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))
	resp, err := client.Do(req)
	if err != nil {
		return groupList, err
	}
	if resp.StatusCode != 200 {
		return groupList, fmt.Errorf("failed to list instance groups, status code: %d", resp.StatusCode)
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return groupList, err
	}

	var getResp listInstanceGroupsResponse
	if err := json.Unmarshal(body, &getResp); err != nil {
		return groupList, err
	}

	for _, result := range getResp.Items {
		for _, group := range result.InstanceGroups {
			if filterPattern.MatchString(group.Name) {
				groupList = append(groupList, group.SelfLink)
			}
		}
	}

	return groupList, nil
}
